-- Additive enum expansion only; never drops question, history or profile data.
ALTER TABLE questions DROP CONSTRAINT IF EXISTS valid_source;
ALTER TABLE questions ADD CONSTRAINT valid_source CHECK (source_type IN ('PYQ','PYQ_PATTERN','ORIGINAL','SUPPLEMENTARY'));
