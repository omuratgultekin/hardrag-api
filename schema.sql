-- HardRAG API Database Schema for Supabase
-- Run this in Supabase SQL Editor

-- ============================================================================
-- Tables
-- ============================================================================

-- Validation requests table (stores all validation API calls)
CREATE TABLE IF NOT EXISTS validation_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    output TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL,
    violations JSONB DEFAULT '[]'::jsonb,
    execution_time_ms FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys table (user API keys)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key TEXT NOT NULL UNIQUE,
    name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- API usage table (for rate limiting and analytics)
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table (additional user metadata)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    company_name TEXT,
    tier TEXT DEFAULT 'free', -- free, starter, enterprise
    monthly_quota INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_validation_requests_user_id 
    ON validation_requests(user_id);

CREATE INDEX IF NOT EXISTS idx_validation_requests_created_at 
    ON validation_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id 
    ON api_keys(user_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_key 
    ON api_keys(key) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_api_usage_user_id_timestamp 
    ON api_usage(user_id, timestamp DESC);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS
ALTER TABLE validation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- validation_requests policies
CREATE POLICY "Users can view own validation requests"
    ON validation_requests FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own validation requests"
    ON validation_requests FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- api_keys policies
CREATE POLICY "Users can view own API keys"
    ON api_keys FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own API keys"
    ON api_keys FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own API keys"
    ON api_keys FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own API keys"
    ON api_keys FOR DELETE
    USING (auth.uid() = user_id);

-- api_usage policies
CREATE POLICY "Users can view own API usage"
    ON api_usage FOR SELECT
    USING (auth.uid() = user_id);

-- user_profiles policies
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, tier, monthly_quota)
    VALUES (NEW.id, 'free', 1000);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update last_used_at for API keys
CREATE OR REPLACE FUNCTION public.update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE api_keys
    SET last_used_at = NOW()
    WHERE key = NEW.key;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Note: Run these manually after creating a test user
-- Replace 'your-user-id' with actual user ID from auth.users

-- INSERT INTO api_keys (user_id, key, name)
-- VALUES ('your-user-id', 'sk_test_1234567890', 'Test API Key');

-- ============================================================================
-- Grants (if needed)
-- ============================================================================

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
