require('dotenv').config();

console.log('=== Lambda Environment Test ===');
console.log('Node Version:', process.version);
console.log('MYSQL_URI present:', !!process.env.MYSQL_URI);
console.log('MYSQL_URI length:', process.env.MYSQL_URI?.length || 0);
console.log('MYSQL_URI (masked):', process.env.MYSQL_URI ?
    process.env.MYSQL_URI.replace(/:[^:@]+@/, ':****@') : 'NOT SET');

// Test database connection
const mysql = require('mysql2/promise');

async function testConnection() {
    try {
        const dbUri = process.env.MYSQL_URI;
        if (!dbUri) {
            throw new Error('MYSQL_URI environment variable is not set');
        }

        // Parse URI
        const regex = /mysql\+mysqlconnector:\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)/;
        const match = dbUri.match(regex);

        if (!match) {
            throw new Error('Invalid MySQL URI format');
        }

        const config = {
            user: match[1],
            password: match[2],
            host: match[3],
            port: parseInt(match[4]),
            database: match[5],
            connectTimeout: 10000
        };

        console.log('\n=== Connection Config ===');
        console.log('Host:', config.host);
        console.log('Port:', config.port);
        console.log('Database:', config.database);
        console.log('User:', config.user);

        console.log('\n=== Testing Connection ===');
        const connection = await mysql.createConnection(config);
        console.log('✅ Connected successfully!');

        const [rows] = await connection.query('SELECT 1 as test');
        console.log('✅ Query test:', rows);

        await connection.end();
        console.log('✅ Connection closed');

        return { success: true, message: 'Database connection successful' };
    } catch (error) {
        console.error('❌ Connection failed:', error.message);
        console.error('Error code:', error.code);
        console.error('Error stack:', error.stack);
        return { success: false, error: error.message, code: error.code };
    }
}

// Lambda handler for testing
exports.handler = async (event) => {
    console.log('Event:', JSON.stringify(event, null, 2));
    const result = await testConnection();
    return {
        statusCode: result.success ? 200 : 500,
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify(result, null, 2)
    };
};

// Run if executed directly
if (require.main === module) {
    testConnection().then(() => process.exit(0));
}
