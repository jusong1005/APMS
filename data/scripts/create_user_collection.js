const database = db.getSiblingDB('agri_price')

const userValidator = {
  $jsonSchema: {
    bsonType: 'object',
    required: ['username', 'password', 'role', 'create_time', 'update_time'],
    properties: {
      id: { bsonType: ['int', 'long'], description: '用户 ID，可由后端生成自增或业务编号' },
      username: { bsonType: 'string', minLength: 2, maxLength: 50, description: '用户名，唯一' },
      password: { bsonType: 'string', minLength: 20, maxLength: 120, description: '加密后的密码摘要' },
      role: { bsonType: 'string', enum: ['farmer', 'dealer', 'admin', 'analyst', 'user'], description: '用户角色' },
      phone: { bsonType: ['string', 'null'], maxLength: 20, description: '手机号' },
      email: { bsonType: ['string', 'null'], maxLength: 100, description: '邮箱' },
      create_time: { bsonType: 'date', description: '创建时间' },
      update_time: { bsonType: 'date', description: '更新时间' }
    }
  }
}

if (!database.getCollectionNames().includes('user')) {
  database.createCollection('user', {
    validator: userValidator,
    validationLevel: 'moderate'
  })
} else {
  database.runCommand({
    collMod: 'user',
    validator: userValidator,
    validationLevel: 'moderate'
  })
}

database.user.createIndex({ id: 1 }, { unique: true, sparse: true, name: 'uk_user_id' })
database.user.createIndex({ username: 1 }, { unique: true, name: 'uk_user_username' })
database.user.createIndex({ phone: 1 }, { unique: true, sparse: true, name: 'uk_user_phone' })
database.user.createIndex({ email: 1 }, { unique: true, sparse: true, name: 'uk_user_email' })
database.user.createIndex({ role: 1, create_time: -1 }, { name: 'idx_user_role_create_time' })

printjson({
  database: database.getName(),
  collection: 'user',
  indexes: database.user.getIndexes().map((index) => index.name)
})