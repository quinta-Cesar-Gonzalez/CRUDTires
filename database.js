require('dotenv').config();
const mysql = require('mysql2/promise');

// Parse MySQL URI
function parseDbUri(uri) {
  // Format: mysql+mysqlconnector://user:pass@host:port/database
  const regex = /mysql\+mysqlconnector:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)/;
  const match = uri.match(regex);
  
  if (!match) {
    throw new Error('Invalid MySQL URI format');
  }
  
  return {
    user: match[1],
    password: match[2],
    host: match[3],
    port: parseInt(match[4]),
    database: match[5]
  };
}

// Lambda-optimized connection pool settings
const dbConfig = parseDbUri(process.env.MYSQL_URI);
const poolConfig = {
  ...dbConfig,
  waitForConnections: true,
  connectionLimit: 1, // Lambda optimization: 1 connection per container
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 0,
  connectTimeout: 10000,
  // Reuse connections across Lambda invocations
  maxIdle: 1,
  idleTimeout: 60000
};

// Global connection pool (reused across Lambda invocations)
let pool = null;

function getPool() {
  if (!pool) {
    pool = mysql.createPool(poolConfig);
  }
  return pool;
}

// Execute query with error handling
async function query(sql, params = []) {
  const connection = await getPool().getConnection();
  try {
    const [results] = await connection.query(sql, params);
    return results;
  } finally {
    connection.release();
  }
}

// Get a single row
async function queryOne(sql, params = []) {
  const results = await query(sql, params);
  return results.length > 0 ? results[0] : null;
}

module.exports = {
  getPool,
  query,
  queryOne
};
