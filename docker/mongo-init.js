// ============================================================
// MongoDB Initialization Script for ReplicarIA
// ============================================================

// Switch to the agent_network database
db = db.getSiblingDB('agent_network');

// Create collections with validation
db.createCollection('projects', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['project_id', 'project_name', 'status'],
      properties: {
        project_id: { bsonType: 'string' },
        project_name: { bsonType: 'string' },
        status: { bsonType: 'string' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('agent_interactions');
db.createCollection('validation_reports');
db.createCollection('purchase_orders');
db.createCollection('vbc_records');
db.createCollection('payments');
db.createCollection('deliberations');

// Create indexes for better performance
db.projects.createIndex({ 'project_id': 1 }, { unique: true });
db.projects.createIndex({ 'status': 1 });
db.projects.createIndex({ 'created_at': -1 });

db.agent_interactions.createIndex({ 'project_id': 1 });
db.agent_interactions.createIndex({ 'timestamp': -1 });
db.agent_interactions.createIndex({ 'interaction_id': 1 }, { unique: true });

db.validation_reports.createIndex({ 'project_id': 1 });
db.purchase_orders.createIndex({ 'project_id': 1 });
db.vbc_records.createIndex({ 'project_id': 1 });
db.payments.createIndex({ 'project_id': 1 });
db.deliberations.createIndex({ 'project_id': 1 });

print('MongoDB initialized successfully for ReplicarIA');
