-- Additive upgrade for existing databases. Also runs after the initial schema.
-- Do not reconstruct provenance for old runs from mutable current profiles.
ALTER TABLE prediction_runs ADD COLUMN IF NOT EXISTS inference_context JSONB;

CREATE OR REPLACE FUNCTION protect_prediction_snapshot() RETURNS trigger AS $$
BEGIN
    IF NEW IS DISTINCT FROM OLD AND EXISTS (
        SELECT 1 FROM prediction_runs WHERE snapshot_id = OLD.id
    ) THEN
        RAISE EXCEPTION 'Snapshot used by a prediction is immutable; create a new snapshot'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protect_prediction_snapshot ON student_feature_snapshots;
CREATE TRIGGER protect_prediction_snapshot BEFORE UPDATE ON student_feature_snapshots
FOR EACH ROW EXECUTE FUNCTION protect_prediction_snapshot();

CREATE OR REPLACE FUNCTION protect_prediction_context() RETURNS trigger AS $$
BEGIN
    IF NEW.snapshot_id IS DISTINCT FROM OLD.snapshot_id
       OR NEW.model_id IS DISTINCT FROM OLD.model_id
       OR NEW.prediction_label IS DISTINCT FROM OLD.prediction_label
       OR NEW.risk_probability IS DISTINCT FROM OLD.risk_probability
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.inference_context IS DISTINCT FROM OLD.inference_context THEN
        RAISE EXCEPTION 'Prediction input, model identity and result are immutable'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protect_prediction_context ON prediction_runs;
CREATE TRIGGER protect_prediction_context BEFORE UPDATE ON prediction_runs
FOR EACH ROW EXECUTE FUNCTION protect_prediction_context();
