START TRANSACTION;

-- Example additive migration: add relationship manager fields.
ALTER TABLE users ADD COLUMN IF NOT EXISTS relationship_manager VARCHAR(120);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS branch_code VARCHAR(20);

COMMIT;
