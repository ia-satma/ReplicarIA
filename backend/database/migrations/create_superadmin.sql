-- Superadmin user creation for santiago@satma.mx
-- Run this in the Neon console or via psql

INSERT INTO auth_users (email, full_name, password_hash, role, status, auth_method, email_verified, metadata)
VALUES (
  'santiago@satma.mx',
  'Santiago - Super Admin',
  '$2b$12$XUB/b01prfamrc7YEtbJIOu82mfTgjBTDisXROR.LmcoOijGoDlVu',
  'super_admin',
  'active',
  'password',
  true,
  '{"can_see_devils_advocate": true}'::jsonb
)
ON CONFLICT (email) DO UPDATE SET
  password_hash = EXCLUDED.password_hash,
  role = EXCLUDED.role,
  auth_method = EXCLUDED.auth_method,
  status = EXCLUDED.status,
  email_verified = EXCLUDED.email_verified,
  metadata = EXCLUDED.metadata
RETURNING id, email, role, auth_method;
