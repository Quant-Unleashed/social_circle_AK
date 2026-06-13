create table if not exists profiles (
  email text primary key,
  name text not null,
  username text not null,
  avatar_url text default '',
  role text not null default 'member',
  created_at timestamptz not null default now()
);

create table if not exists groups (
  id text primary key,
  name text not null,
  description text not null default '',
  enabled_modules jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists memberships (
  email text not null references profiles(email) on delete cascade,
  group_id text not null references groups(id) on delete cascade,
  role text not null default 'member',
  primary key (email, group_id)
);

create table if not exists invite_codes (
  code text primary key,
  group_ids jsonb not null,
  role text not null default 'member'
);

create table if not exists activity (
  id text primary key,
  group_id text not null references groups(id) on delete cascade,
  type text not null,
  message text not null,
  created_at timestamptz not null default now()
);

create table if not exists sports_players (
  id text primary key,
  group_id text not null references groups(id) on delete cascade,
  name text not null,
  ladder_rank integer not null,
  elo integer not null default 1200
);

create table if not exists sports_matches (
  id text primary key,
  group_id text not null references groups(id) on delete cascade,
  sport text not null,
  winner_id text,
  loser_id text,
  score text default '',
  status text not null default 'confirmed',
  created_by text references profiles(email),
  created_at timestamptz not null default now()
);

create table if not exists tennis_sessions (
  id text primary key,
  group_id text not null references groups(id) on delete cascade,
  state jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists events (
  id text primary key,
  group_id text not null references groups(id) on delete cascade,
  title text not null,
  starts_at text default '',
  location text default '',
  description text default '',
  rsvps jsonb not null default '{}'::jsonb,
  bring_items jsonb not null default '[]'::jsonb,
  polls jsonb not null default '[]'::jsonb,
  costs jsonb not null default '[]'::jsonb,
  dietary_notes text default '',
  comments jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists life_entries (
  id text primary key,
  email text not null references profiles(email) on delete cascade,
  group_id text not null references groups(id) on delete cascade,
  category text not null,
  title text not null,
  body text default '',
  visibility text not null check (visibility in ('only_me', 'selected_group', 'friends', 'family')),
  created_at timestamptz not null default now()
);

create table if not exists relationship_notes (
  id text primary key,
  author_email text not null references profiles(email) on delete cascade,
  subject_email text not null references profiles(email) on delete cascade,
  body text not null,
  shared boolean not null default false,
  created_at timestamptz not null default now()
);

alter table profiles enable row level security;
alter table groups enable row level security;
alter table memberships enable row level security;
alter table invite_codes enable row level security;
alter table activity enable row level security;
alter table sports_players enable row level security;
alter table sports_matches enable row level security;
alter table tennis_sessions enable row level security;
alter table events enable row level security;
alter table life_entries enable row level security;
alter table relationship_notes enable row level security;
