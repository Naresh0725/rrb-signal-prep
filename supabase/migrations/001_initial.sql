-- SignalPrep schema. Apply once in Supabase SQL Editor before starting production.
BEGIN;

CREATE TABLE profiles (
	id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	role VARCHAR NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE question_sources (
	id VARCHAR NOT NULL, 
	reference TEXT NOT NULL, 
	verified BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE question_topics (
	id VARCHAR NOT NULL, 
	subject VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (subject, name)
)

;

CREATE TABLE test_configs (
	id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	distribution JSON NOT NULL, 
	duration_minutes INTEGER NOT NULL, 
	source_mix JSON NOT NULL, 
	difficulty_mix JSON NOT NULL, 
	cooldown_days INTEGER NOT NULL, 
	correct_marks FLOAT NOT NULL, 
	wrong_penalty FLOAT NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE question_generation_jobs (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	request JSON NOT NULL, 
	output JSON NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;
CREATE INDEX ix_question_generation_jobs_user_id ON question_generation_jobs (user_id);

CREATE TABLE questions (
	id VARCHAR NOT NULL, 
	question_text TEXT NOT NULL, 
	option_a TEXT NOT NULL, 
	option_b TEXT NOT NULL, 
	option_c TEXT NOT NULL, 
	option_d TEXT NOT NULL, 
	correct_option VARCHAR NOT NULL, 
	explanation TEXT NOT NULL, 
	subject VARCHAR NOT NULL, 
	topic VARCHAR NOT NULL, 
	subtopic VARCHAR NOT NULL, 
	topic_id VARCHAR, 
	source_id VARCHAR, 
	difficulty VARCHAR NOT NULL, 
	source_type VARCHAR NOT NULL, 
	source_reference TEXT NOT NULL, 
	verification_status VARCHAR NOT NULL, 
	exam VARCHAR NOT NULL, 
	exam_year INTEGER, 
	shift VARCHAR NOT NULL, 
	parent_question_id VARCHAR, 
	generation_method VARCHAR NOT NULL, 
	generation_metadata JSON NOT NULL, 
	status VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	updated_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(topic_id) REFERENCES question_topics (id), 
	FOREIGN KEY(source_id) REFERENCES question_sources (id), 
	FOREIGN KEY(parent_question_id) REFERENCES questions (id)
)

;
CREATE INDEX ix_questions_status ON questions (status);
CREATE INDEX ix_questions_subject ON questions (subject);
CREATE INDEX ix_questions_topic ON questions (topic);
CREATE INDEX ix_questions_source_type ON questions (source_type);

CREATE TABLE test_attempts (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	config_id VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	mode VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	started_at VARCHAR NOT NULL, 
	deadline VARCHAR NOT NULL, 
	submitted_at VARCHAR, 
	policy JSON NOT NULL, 
	result JSON, 
	version INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(config_id) REFERENCES test_configs (id)
)

;
CREATE INDEX ix_test_attempts_user_id ON test_attempts (user_id);

CREATE TABLE bookmarks (
	user_id VARCHAR NOT NULL, 
	question_id VARCHAR NOT NULL, 
	PRIMARY KEY (user_id, question_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
)

;

CREATE TABLE question_reviews (
	id VARCHAR NOT NULL, 
	question_id VARCHAR NOT NULL, 
	reviewer_id VARCHAR NOT NULL, 
	decision VARCHAR NOT NULL, 
	notes TEXT NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id), 
	FOREIGN KEY(reviewer_id) REFERENCES profiles (id)
)

;

CREATE TABLE test_questions (
	id VARCHAR NOT NULL, 
	attempt_id VARCHAR NOT NULL, 
	question_id VARCHAR NOT NULL, 
	position INTEGER NOT NULL, 
	snapshot JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (attempt_id, position), 
	UNIQUE (attempt_id, question_id), 
	FOREIGN KEY(attempt_id) REFERENCES test_attempts (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
)

;
CREATE INDEX ix_test_questions_attempt_id ON test_questions (attempt_id);

CREATE TABLE user_answers (
	id VARCHAR NOT NULL, 
	attempt_id VARCHAR NOT NULL, 
	question_id VARCHAR NOT NULL, 
	selected VARCHAR, 
	marked BOOLEAN NOT NULL, 
	visited BOOLEAN NOT NULL, 
	first_selected VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (attempt_id, question_id), 
	FOREIGN KEY(attempt_id) REFERENCES test_attempts (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
)

;
CREATE INDEX ix_user_answers_attempt_id ON user_answers (attempt_id);

ALTER TABLE profiles ADD CONSTRAINT valid_role CHECK (role IN ('student','admin'));
ALTER TABLE questions ADD CONSTRAINT valid_source CHECK (source_type IN ('PYQ','PYQ_PATTERN','ORIGINAL'));
ALTER TABLE questions ADD CONSTRAINT valid_status CHECK (status IN ('ACTIVE','PENDING_REVIEW','REJECTED','ARCHIVED'));
ALTER TABLE questions ADD CONSTRAINT valid_answer CHECK (correct_option IN ('A','B','C','D'));
ALTER TABLE questions ADD CONSTRAINT valid_difficulty CHECK (difficulty IN ('Easy','Medium','Hard'));
ALTER TABLE questions ADD CONSTRAINT verified_pyq_only CHECK (source_type <> 'PYQ' OR (verification_status='VERIFIED_PYQ' AND length(source_reference)>0 AND exam_year IS NOT NULL));
ALTER TABLE test_attempts ADD CONSTRAINT valid_mode CHECK (mode IN ('EXAM','PRACTICE'));
ALTER TABLE test_attempts ADD CONSTRAINT valid_attempt_status CHECK (status IN ('IN_PROGRESS','SUBMITTED'));
CREATE INDEX question_filter_idx ON questions(status,subject,source_type,difficulty);
CREATE INDEX attempt_user_status_idx ON test_attempts(user_id,status);
CREATE INDEX question_text_search_idx ON questions USING gin(to_tsvector('english', question_text));
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON profiles FROM anon, authenticated;
ALTER TABLE question_sources ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON question_sources FROM anon, authenticated;
ALTER TABLE question_topics ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON question_topics FROM anon, authenticated;
ALTER TABLE test_configs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON test_configs FROM anon, authenticated;
ALTER TABLE question_generation_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON question_generation_jobs FROM anon, authenticated;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON questions FROM anon, authenticated;
ALTER TABLE test_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON test_attempts FROM anon, authenticated;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON bookmarks FROM anon, authenticated;
ALTER TABLE question_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON question_reviews FROM anon, authenticated;
ALTER TABLE test_questions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON test_questions FROM anon, authenticated;
ALTER TABLE user_answers ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON user_answers FROM anon, authenticated;

-- All writes go through authenticated, authorized FastAPI endpoints.
-- Never grant browser SELECT on question keys or in-progress snapshots.
GRANT SELECT ON profiles,test_attempts,user_answers,bookmarks,test_configs,question_topics TO authenticated;
CREATE POLICY profile_self_read ON profiles FOR SELECT TO authenticated USING (id=auth.uid()::text);
CREATE POLICY attempts_self_read ON test_attempts FOR SELECT TO authenticated USING (user_id=auth.uid()::text);
CREATE POLICY answers_self_read ON user_answers FOR SELECT TO authenticated USING (EXISTS (SELECT 1 FROM test_attempts a WHERE a.id=attempt_id AND a.user_id=auth.uid()::text));
CREATE POLICY bookmarks_self_read ON bookmarks FOR SELECT TO authenticated USING (user_id=auth.uid()::text);
CREATE POLICY configs_read ON test_configs FOR SELECT TO authenticated USING (true);
CREATE POLICY topics_read ON question_topics FOR SELECT TO authenticated USING (true);
CREATE VIEW user_topic_performance WITH (security_invoker=true) AS
 SELECT a.user_id, tq.snapshot->>'topic' AS topic,
 count(*) FILTER (WHERE ua.selected IS NOT NULL) AS attempted,
 count(*) FILTER (WHERE ua.selected=tq.snapshot->>'correct_option') AS correct,
 count(DISTINCT a.id) AS test_count
 FROM test_attempts a JOIN test_questions tq ON tq.attempt_id=a.id
 LEFT JOIN user_answers ua ON ua.attempt_id=a.id AND ua.question_id=tq.question_id
 WHERE a.status='SUBMITTED' AND a.mode='EXAM'
 GROUP BY a.user_id,tq.snapshot->>'topic';
-- View is backend-only because browser roles cannot read snapshots.
REVOKE ALL ON user_topic_performance FROM anon,authenticated;
COMMIT;
