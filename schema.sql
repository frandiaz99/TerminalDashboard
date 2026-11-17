-- Leaderboard del crucigrama hardcore (sync-migrations).
-- Pegar entero en Supabase → SQL Editor → Run. Es idempotente: se puede volver a correr.

create extension if not exists pgcrypto with schema extensions;

-- ───────────── tablas ─────────────

create table if not exists public.players (
    id          bigint generated always as identity primary key,
    name        text not null unique check (length(name) between 1 and 24),
    token_hash  text not null unique,            -- sha256 del token, el token en sí no se guarda
    active      boolean not null default true,
    created_at  timestamptz not null default now()
);

create table if not exists public.scores (
    id           bigint generated always as identity primary key,
    player_id    bigint not null references public.players(id) on delete cascade,
    play_date    date not null,
    score        int  not null check (score between 0 and 1300),
    ok           int  not null check (ok >= 0),
    total        int  not null check (total between 1 and 200),
    elapsed      int  not null check (elapsed between 0 and 900),   -- segundos usados
    daily_seen   boolean not null default false,  -- había abierto el básico del día antes
    version      text,
    submitted_at timestamptz not null default now(),
    unique (player_id, play_date),                -- vale el primer envío del día
    check (ok <= total)
);

-- Nadie entra directo a las tablas: RLS sin policies = cerrado para anon/authenticated.
alter table public.players enable row level security;
alter table public.scores  enable row level security;
revoke all on public.players, public.scores from anon, authenticated;

-- ───────────── lectura pública (lo que usa la web) ─────────────

create or replace view public.public_scores as
select p.name, s.play_date, s.score, s.ok, s.total, s.elapsed, s.daily_seen, s.submitted_at
from public.scores s
join public.players p on p.id = s.player_id
where p.active;

create or replace view public.public_players as
select name from public.players where active;

grant select on public.public_scores, public.public_players to anon, authenticated;

-- ───────────── envío desde el script ─────────────

create or replace function public.submit_score(
    p_token      text,
    p_date       date,
    p_score      int,
    p_ok         int,
    p_total      int,
    p_elapsed    int,
    p_daily_seen boolean default false,
    p_version    text default null
) returns json
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_player  bigint;
    v_now     timestamp := now() at time zone 'America/Argentina/Buenos_Aires';
    v_today   date := v_now::date;
    v_ratio   numeric;
    v_expect  int;
    v_id      bigint;
begin
    select id into v_player from players
    where token_hash = encode(digest(coalesce(p_token, ''), 'sha256'), 'hex') and active;
    if v_player is null then
        raise exception 'invalid token' using errcode = 'P0001';
    end if;

    -- solo el crucigrama de hoy (con 30 min de gracia pasada la medianoche)
    if not (p_date = v_today or (p_date = v_today - 1 and v_now::time < time '00:30')) then
        raise exception 'date out of window: %', p_date using errcode = 'P0001';
    end if;
    if extract(isodow from p_date) > 5 then
        raise exception 'weekend' using errcode = 'P0001';
    end if;

    if p_total is null or p_total < 1 or p_ok is null or p_ok < 0 or p_ok > p_total
       or p_elapsed is null or p_elapsed < 0 or p_elapsed > 900 then
        raise exception 'bad payload' using errcode = 'P0001';
    end if;

    -- misma fórmula que Puzzle.submit() en sync.py (se tolera ±2 por redondeo de segundos y .5)
    v_ratio  := p_ok::numeric / p_total;
    v_expect := round(1000 * v_ratio) + round(300 * ((900 - p_elapsed)::numeric / 900) * v_ratio * v_ratio);
    if p_score is null or abs(p_score - v_expect) > 2 then
        raise exception 'score mismatch (expected %)', v_expect using errcode = 'P0001';
    end if;

    insert into scores (player_id, play_date, score, ok, total, elapsed, daily_seen, version)
    values (v_player, p_date, p_score, p_ok, p_total, p_elapsed, coalesce(p_daily_seen, false), left(p_version, 32))
    on conflict (player_id, play_date) do nothing
    returning id into v_id;

    return json_build_object('status', case when v_id is null then 'duplicate' else 'ok' end);
end;
$$;

revoke all on function public.submit_score(text, date, int, int, int, int, boolean, text) from public;
grant execute on function public.submit_score(text, date, int, int, int, int, boolean, text) to anon, authenticated;

-- ───────────── importación de historial (una sola vez por jugador, al cargar el token) ─────────────

alter table public.players add column if not exists backfilled_at timestamptz;

create or replace function public.import_history(p_token text, p_items json) returns json
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_player  bigint;
    v_done    timestamptz;
    v_today   date := (now() at time zone 'America/Argentina/Buenos_Aires')::date;
    v_item    json;
    v_date    date;
    v_ok      int;
    v_total   int;
    v_elapsed int;
    v_score   int;
    v_ratio   numeric;
    v_expect  int;
    v_id      bigint;
    v_added   int := 0;
    v_skipped int := 0;
begin
    select id, backfilled_at into v_player, v_done from players
    where token_hash = encode(digest(coalesce(p_token, ''), 'sha256'), 'hex') and active
    for update;
    if v_player is null then
        raise exception 'invalid token' using errcode = 'P0001';
    end if;
    if v_done is not null then
        return json_build_object('status', 'already_imported', 'at', v_done);
    end if;
    if json_typeof(p_items) <> 'array' or json_array_length(p_items) > 500 then
        raise exception 'bad payload' using errcode = 'P0001';
    end if;

    for v_item in select * from json_array_elements(p_items) loop
        begin
            v_date    := (v_item->>'p_date')::date;
            v_score   := (v_item->>'p_score')::int;
            v_ok      := (v_item->>'p_ok')::int;
            v_total   := (v_item->>'p_total')::int;
            v_elapsed := (v_item->>'p_elapsed')::int;
            v_ratio   := v_ok::numeric / v_total;
            v_expect  := round(1000 * v_ratio) + round(300 * ((900 - v_elapsed)::numeric / 900) * v_ratio * v_ratio);
            if v_date > v_today or extract(isodow from v_date) > 5
               or v_ok < 0 or v_ok > v_total or v_elapsed < 0 or v_elapsed > 900
               or abs(v_score - v_expect) > 2 then
                v_skipped := v_skipped + 1;
                continue;
            end if;
            insert into scores (player_id, play_date, score, ok, total, elapsed, daily_seen, version)
            values (v_player, v_date, v_score, v_ok, v_total, v_elapsed,
                    coalesce((v_item->>'p_daily_seen')::boolean, false), left(v_item->>'p_version', 32))
            on conflict (player_id, play_date) do nothing
            returning id into v_id;
            if v_id is null then v_skipped := v_skipped + 1; else v_added := v_added + 1; end if;
        exception when others then
            v_skipped := v_skipped + 1;   -- ítem mal formado: se saltea, no corta la importación
        end;
    end loop;

    update players set backfilled_at = now() where id = v_player;
    return json_build_object('status', 'ok', 'added', v_added, 'skipped', v_skipped);
end;
$$;

revoke all on function public.import_history(text, json) from public;
grant execute on function public.import_history(text, json) to anon, authenticated;

-- Para dejar que alguien vuelva a importar:  update players set backfilled_at = null where name = 'Nico';

-- ───────────── alta de jugadores (solo desde el SQL Editor) ─────────────
-- select public.add_player('Nico');   → devuelve el token para pasarle a esa persona

create or replace function public.add_player(p_name text) returns text
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    v_token text := encode(gen_random_bytes(16), 'hex');
begin
    insert into players (name, token_hash)
    values (p_name, encode(digest(v_token, 'sha256'), 'hex'))
    on conflict (name) do update set token_hash = excluded.token_hash, active = true;  -- re-emitir token
    return v_token;
end;
$$;

revoke all on function public.add_player(text) from public, anon, authenticated;
