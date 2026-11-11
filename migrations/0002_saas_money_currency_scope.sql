-- SPEC-003 (2026-11-11): exact money, ISO 4217 currency, workspace-defined scope (cash-flow).
-- Amounts move from double precision to numeric; currency codes must be three upper-case letters;
-- owner_scope (the owner's own life areas) becomes scope, a free label each workspace defines.
-- Append-only: do not edit once applied.

-- cashflow-plan
ALTER TABLE cash_flow.cashflow_plans NO FORCE ROW LEVEL SECURITY;
UPDATE cash_flow.cashflow_plans SET currency = upper(btrim(currency));
ALTER TABLE cash_flow.cashflow_plans FORCE ROW LEVEL SECURITY;
ALTER TABLE cash_flow.cashflow_plans RENAME COLUMN owner_scope TO scope;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'cash_flow.cashflow_plans'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'cash_flow.cashflow_plans'::regclass AND attname = 'scope')] LOOP EXECUTE format('ALTER TABLE cash_flow.cashflow_plans DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE cash_flow.cashflow_plans ALTER COLUMN scope SET DEFAULT '';
ALTER TABLE cash_flow.cashflow_plans ADD CONSTRAINT cashflow_plans_scope_check CHECK (length(scope) <= 64);
DO $$ DECLARE i text; BEGIN SELECT indexname INTO i FROM pg_indexes WHERE schemaname = 'cash_flow' AND tablename = 'cashflow_plans' AND indexdef LIKE '%(workspace_id, scope)'; IF i IS NOT NULL THEN EXECUTE format('ALTER INDEX cash_flow.%I RENAME TO cashflow_plans_scope', i); END IF; END $$;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'cash_flow.cashflow_plans'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'cash_flow.cashflow_plans'::regclass AND attname = 'expected_inflow')] LOOP EXECUTE format('ALTER TABLE cash_flow.cashflow_plans DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE cash_flow.cashflow_plans ALTER COLUMN expected_inflow TYPE numeric(19,4) USING expected_inflow::numeric(19,4);
ALTER TABLE cash_flow.cashflow_plans ADD CONSTRAINT cashflow_plans_expected_inflow_check CHECK (expected_inflow >= 0);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'cash_flow.cashflow_plans'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'cash_flow.cashflow_plans'::regclass AND attname = 'expected_outflow')] LOOP EXECUTE format('ALTER TABLE cash_flow.cashflow_plans DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE cash_flow.cashflow_plans ALTER COLUMN expected_outflow TYPE numeric(19,4) USING expected_outflow::numeric(19,4);
ALTER TABLE cash_flow.cashflow_plans ADD CONSTRAINT cashflow_plans_expected_outflow_check CHECK (expected_outflow >= 0);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'cash_flow.cashflow_plans'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'cash_flow.cashflow_plans'::regclass AND attname = 'reserve_target')] LOOP EXECUTE format('ALTER TABLE cash_flow.cashflow_plans DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE cash_flow.cashflow_plans ALTER COLUMN reserve_target TYPE numeric(19,4) USING reserve_target::numeric(19,4);
ALTER TABLE cash_flow.cashflow_plans ADD CONSTRAINT cashflow_plans_reserve_target_check CHECK (reserve_target IS NULL OR (reserve_target >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'cash_flow.cashflow_plans'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'cash_flow.cashflow_plans'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE cash_flow.cashflow_plans DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE cash_flow.cashflow_plans ADD CONSTRAINT cashflow_plans_currency_check CHECK (currency ~ '^[A-Z]{3}$');
