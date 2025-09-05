-- Supabase PMS Schema (80/20)
-- Idempotent: safe to run multiple times

-- Extensions
create extension if not exists pgcrypto;

-- ======================================
-- 1) chemical_types (Type Layer – Generic)
-- ======================================
create table if not exists public.chemical_types (
  id uuid primary key default gen_random_uuid(),
  name text,
  category text,
  hs_code text,
  applications text[],
  spec_template jsonb,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- Ensure columns exist (add-only)
alter table public.chemical_types add column if not exists name text;
alter table public.chemical_types add column if not exists category text;
alter table public.chemical_types add column if not exists hs_code text;
alter table public.chemical_types add column if not exists applications text[];
alter table public.chemical_types add column if not exists spec_template jsonb;
alter table public.chemical_types add column if not exists metadata jsonb;
alter table public.chemical_types add column if not exists created_at timestamptz not null default now();

create index if not exists idx_chem_types_name on public.chemical_types (name);

-- ======================================
-- 2) tds_unique_chemicals (Entity Layer – Brand/Grade)
-- ======================================
create table if not exists public.tds_unique_chemicals (
  id uuid primary key default gen_random_uuid(),
  chemical_type_id uuid not null references public.chemical_types(id) on delete cascade,
  brand text,
  grade text,
  owner text,
  source text,
  specs jsonb,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_tds_entity_type on public.tds_unique_chemicals (chemical_type_id);
create index if not exists idx_tds_entity_brand_grade on public.tds_unique_chemicals (brand, grade);

-- ======================================
-- 3) market_opportunities (Demand)
-- ======================================
create table if not exists public.market_opportunities (
  id uuid primary key default gen_random_uuid(),
  organization text,
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  period date not null,
  volume_ton numeric,
  price_usd_per_ton numeric,
  local_price_per_kg numeric,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now(),
  unique (organization, chemical_entity_id, period)
);

create index if not exists idx_market_entity_period on public.market_opportunities (chemical_entity_id, period);
create index if not exists idx_market_org on public.market_opportunities (organization);

-- ======================================
-- 4) tds_sourcing_data (Supply)
-- ======================================
create table if not exists public.tds_sourcing_data (
  id uuid primary key default gen_random_uuid(),
  supplier text not null,
  partner text,
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  incoterm text,
  lane text,
  price_usd_per_ton numeric,
  terms text,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_tds_sourcing_entity on public.tds_sourcing_data (chemical_entity_id);
create index if not exists idx_tds_sourcing_supplier on public.tds_sourcing_data (supplier);

-- ======================================
-- 5) leanchems_products (Portfolio)
-- ======================================
create table if not exists public.leanchems_products (
  id uuid primary key default gen_random_uuid(),
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  alias_name text,
  business_models text[],
  selling_price_usd_per_ton numeric,
  unique_value_proposition text,
  risks text,
  stock_status jsonb,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_portfolio_entity on public.leanchems_products (chemical_entity_id);
create unique index if not exists uq_portfolio_alias on public.leanchems_products (alias_name) where alias_name is not null;

-- ======================================
-- Row Level Security (RLS) + Policies
-- ======================================
alter table public.chemical_types enable row level security;
alter table public.tds_unique_chemicals enable row level security;
alter table public.market_opportunities enable row level security;
alter table public.tds_sourcing_data enable row level security;
alter table public.leanchems_products enable row level security;

do $$
begin
  if not exists (select 1 from pg_policies where tablename='chemical_types' and policyname='chemical_types_all_auth') then
    create policy chemical_types_all_auth on public.chemical_types for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='tds_unique_chemicals' and policyname='tds_unique_all_auth') then
    create policy tds_unique_all_auth on public.tds_unique_chemicals for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='market_opportunities' and policyname='market_opps_all_auth') then
    create policy market_opps_all_auth on public.market_opportunities for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='tds_sourcing_data' and policyname='tds_sourcing_all_auth') then
    create policy tds_sourcing_all_auth on public.tds_sourcing_data for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='leanchems_products' and policyname='leanchems_products_all_auth') then
    create policy leanchems_products_all_auth on public.leanchems_products for all to authenticated using (true) with check (true);
  end if;
end $$;

-- End of PMS schema

-- Supabase 80/20 Product Management Schema
-- Idempotent migration: safe to run multiple times

-- Extensions
create extension if not exists pgcrypto;

-- 1) chemical_types (Type Layer – Generic)
create table if not exists public.chemical_types (
  id uuid primary key default gen_random_uuid(),
  name text,
  category text,
  hs_code text,
  applications text[],
  spec_template jsonb,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- Ensure mandatory column presence (add-only)
alter table public.chemical_types add column if not exists name text;
alter table public.chemical_types add column if not exists category text;
alter table public.chemical_types add column if not exists hs_code text;
alter table public.chemical_types add column if not exists applications text[];
alter table public.chemical_types add column if not exists spec_template jsonb;
alter table public.chemical_types add column if not exists metadata jsonb;
alter table public.chemical_types add column if not exists created_at timestamptz not null default now();

create index if not exists idx_chem_types_name on public.chemical_types (name);

-- Backfill name from legacy generic_name if exists
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'chemical_types' and column_name = 'generic_name'
  ) then
    update public.chemical_types
      set name = coalesce(name, generic_name)
      where name is null and coalesce(generic_name, '') <> '';
  end if;
end $$;

-- 2) tds_unique_chemicals (Entity Layer – Brand/Grade)
create table if not exists public.tds_unique_chemicals (
  id uuid primary key default gen_random_uuid(),
  chemical_type_id uuid not null references public.chemical_types(id) on delete cascade,
  brand text,
  grade text,
  owner text,
  source text,
  specs jsonb,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_tds_entity_type on public.tds_unique_chemicals (chemical_type_id);
create index if not exists idx_tds_entity_brand_grade on public.tds_unique_chemicals (brand, grade);

-- 3) market_opportunities (Entity Layer 1 – Demand)
create table if not exists public.market_opportunities (
  id uuid primary key default gen_random_uuid(),
  organization text,
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  period date not null,
  volume_ton numeric,
  price_usd_per_ton numeric,
  local_price_per_kg numeric,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now(),
  unique (organization, chemical_entity_id, period)
);

create index if not exists idx_market_entity_period on public.market_opportunities (chemical_entity_id, period);
create index if not exists idx_market_org on public.market_opportunities (organization);

-- 4) sourcing_partners (Entity Layer 2 – Supply)
create table if not exists public.sourcing_partners (
  id uuid primary key default gen_random_uuid(),
  supplier text not null,
  partner text,
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  incoterm text,
  lane text,
  price_usd_per_ton numeric,
  terms text,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_sourcing_entity on public.sourcing_partners (chemical_entity_id);
create index if not exists idx_sourcing_supplier on public.sourcing_partners (supplier);

-- 5) leanchems_products (Entity Layer 3 – LeanChems Portfolio)
create table if not exists public.leanchems_products (
  id uuid primary key default gen_random_uuid(),
  chemical_entity_id uuid not null references public.tds_unique_chemicals(id) on delete cascade,
  alias_name text,
  business_models text[],
  selling_price_usd_per_ton numeric,
  unique_value_proposition text,
  risks text,
  stock_status jsonb,
  trust_score int,
  value_score int,
  raw_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_portfolio_entity on public.leanchems_products (chemical_entity_id);
create unique index if not exists uq_portfolio_alias on public.leanchems_products (alias_name) where alias_name is not null;

-- --------------------------
-- Row Level Security (RLS)
-- --------------------------
alter table public.chemical_types enable row level security;
alter table public.tds_unique_chemicals enable row level security;
alter table public.market_opportunities enable row level security;
alter table public.sourcing_partners enable row level security;
alter table public.leanchems_products enable row level security;

-- Minimal permissive policies for authenticated users (adjust later)
do $$
begin
  if not exists (select 1 from pg_policies where tablename='chemical_types' and policyname='all_chemical_types_auth') then
    create policy all_chemical_types_auth on public.chemical_types for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='tds_unique_chemicals' and policyname='all_tds_unique_chemicals_auth') then
    create policy all_tds_unique_chemicals_auth on public.tds_unique_chemicals for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='market_opportunities' and policyname='all_market_opportunities_auth') then
    create policy all_market_opportunities_auth on public.market_opportunities for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='sourcing_partners' and policyname='all_sourcing_partners_auth') then
    create policy all_sourcing_partners_auth on public.sourcing_partners for all to authenticated using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='leanchems_products' and policyname='all_leanchems_products_auth') then
    create policy all_leanchems_products_auth on public.leanchems_products for all to authenticated using (true) with check (true);
  end if;
end $$;

-- End of schema


