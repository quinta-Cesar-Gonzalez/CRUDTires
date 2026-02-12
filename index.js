require('dotenv').config();
const express = require('express');
const serverless = require('serverless-http');
const cors = require('cors');
const path = require('path');
const db = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// ===== API ENDPOINTS =====

// GET /api/tires - List tires with pagination, search, and filters
app.get('/api/tires', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const offset = (page - 1) * limit;
        const search = req.query.search || '';
        const { brand, model, size, position } = req.query;

        // Build query
        let whereConditions = [];
        let params = [];

        if (search) {
            whereConditions.push('(brand LIKE ? OR model LIKE ? OR size LIKE ?)');
            params.push(`%${search}%`, `%${search}%`, `%${search}%`);
        }

        if (brand) {
            whereConditions.push('brand = ?');
            params.push(brand);
        }

        if (model) {
            whereConditions.push('model = ?');
            params.push(model);
        }

        if (size) {
            whereConditions.push('size = ?');
            params.push(size);
        }

        if (position) {
            whereConditions.push('position = ?');
            params.push(position);
        }

        const whereClause = whereConditions.length > 0
            ? 'WHERE ' + whereConditions.join(' AND ')
            : '';

        // Get total count
        const countQuery = `SELECT COUNT(*) as total FROM tires_catalog ${whereClause}`;
        const countResult = await db.queryOne(countQuery, params);
        const total = countResult.total;

        // Get paginated data
        const dataQuery = `
      SELECT * FROM tires_catalog 
      ${whereClause}
      ORDER BY id DESC
      LIMIT ? OFFSET ?
    `;
        const tires = await db.query(dataQuery, [...params, limit, offset]);

        res.json({
            success: true,
            data: tires,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.ceil(total / limit)
            }
        });
    } catch (error) {
        console.error('Error fetching tires:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch tires',
            message: error.message
        });
    }
});

// GET /api/tires/:id - Get single tire
app.get('/api/tires/:id', async (req, res) => {
    try {
        const tire = await db.queryOne(
            'SELECT * FROM tires_catalog WHERE id = ?',
            [req.params.id]
        );

        if (!tire) {
            return res.status(404).json({
                success: false,
                error: 'Tire not found'
            });
        }

        res.json({ success: true, data: tire });
    } catch (error) {
        console.error('Error fetching tire:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch tire',
            message: error.message
        });
    }
});

// POST /api/tires - Create new tire
app.post('/api/tires', async (req, res) => {
    try {
        const {
            brand, model, size, layer_index, layers, max_pressure, min_pressure,
            max_depth, min_depth, wear_type, profitability, performance,
            temperature, speed, speed_number, braking, load_type, _load,
            road_type, terrain_type, position
        } = req.body;

        // Validate required fields
        if (!brand || !model || !size) {
            return res.status(400).json({
                success: false,
                error: 'Brand, model, and size are required'
            });
        }

        const query = `
      INSERT INTO tires_catalog (
        brand, model, size, layer_index, layers, max_pressure, min_pressure,
        max_depth, min_depth, wear_type, profitability, performance,
        temperature, speed, speed_number, braking, load_type, _load,
        road_type, terrain_type, position
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

        const params = [
            brand, model, size, layer_index || '', layers || 0, max_pressure || 0,
            min_pressure || 0, max_depth || 0, min_depth || 0, wear_type || null,
            profitability || 0, performance || 0, temperature || '', speed || '',
            speed_number || 0, braking || '', load_type || '', _load || 0,
            road_type || '', terrain_type || '', position || null
        ];

        const result = await db.query(query, params);

        res.status(201).json({
            success: true,
            data: { id: result.insertId },
            message: 'Tire created successfully'
        });
    } catch (error) {
        console.error('Error creating tire:', error);

        // Handle duplicate key error
        if (error.code === 'ER_DUP_ENTRY') {
            return res.status(409).json({
                success: false,
                error: 'A tire with this brand, model, size, and position already exists'
            });
        }

        res.status(500).json({
            success: false,
            error: 'Failed to create tire',
            message: error.message
        });
    }
});

// PUT /api/tires/:id - Update tire
app.put('/api/tires/:id', async (req, res) => {
    try {
        const {
            brand, model, size, layer_index, layers, max_pressure, min_pressure,
            max_depth, min_depth, wear_type, profitability, performance,
            temperature, speed, speed_number, braking, load_type, _load,
            road_type, terrain_type, position
        } = req.body;

        // Validate required fields
        if (!brand || !model || !size) {
            return res.status(400).json({
                success: false,
                error: 'Brand, model, and size are required'
            });
        }

        const query = `
      UPDATE tires_catalog SET
        brand = ?, model = ?, size = ?, layer_index = ?, layers = ?,
        max_pressure = ?, min_pressure = ?, max_depth = ?, min_depth = ?,
        wear_type = ?, profitability = ?, performance = ?, temperature = ?,
        speed = ?, speed_number = ?, braking = ?, load_type = ?, _load = ?,
        road_type = ?, terrain_type = ?, position = ?,
        updated_at = UNIX_TIMESTAMP() * 1000
      WHERE id = ?
    `;

        const params = [
            brand, model, size, layer_index || '', layers || 0, max_pressure || 0,
            min_pressure || 0, max_depth || 0, min_depth || 0, wear_type || null,
            profitability || 0, performance || 0, temperature || '', speed || '',
            speed_number || 0, braking || '', load_type || '', _load || 0,
            road_type || '', terrain_type || '', position || null,
            req.params.id
        ];

        const result = await db.query(query, params);

        if (result.affectedRows === 0) {
            return res.status(404).json({
                success: false,
                error: 'Tire not found'
            });
        }

        res.json({
            success: true,
            message: 'Tire updated successfully'
        });
    } catch (error) {
        console.error('Error updating tire:', error);

        if (error.code === 'ER_DUP_ENTRY') {
            return res.status(409).json({
                success: false,
                error: 'A tire with this brand, model, size, and position already exists'
            });
        }

        res.status(500).json({
            success: false,
            error: 'Failed to update tire',
            message: error.message
        });
    }
});

// DELETE /api/tires/:id - Delete tire
app.delete('/api/tires/:id', async (req, res) => {
    try {
        const result = await db.query(
            'DELETE FROM tires_catalog WHERE id = ?',
            [req.params.id]
        );

        if (result.affectedRows === 0) {
            return res.status(404).json({
                success: false,
                error: 'Tire not found'
            });
        }

        res.json({
            success: true,
            message: 'Tire deleted successfully'
        });
    } catch (error) {
        console.error('Error deleting tire:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete tire',
            message: error.message
        });
    }
});

// GET /api/filters - Get unique values for filters
app.get('/api/filters', async (req, res) => {
    try {
        const brands = await db.query('SELECT DISTINCT brand FROM tires_catalog ORDER BY brand');
        const models = await db.query('SELECT DISTINCT model FROM tires_catalog ORDER BY model');
        const sizes = await db.query('SELECT DISTINCT size FROM tires_catalog ORDER BY size');
        const positions = await db.query('SELECT DISTINCT position FROM tires_catalog WHERE position IS NOT NULL ORDER BY position');

        res.json({
            success: true,
            data: {
                brands: brands.map(r => r.brand),
                models: models.map(r => r.model),
                sizes: sizes.map(r => r.size),
                positions: positions.map(r => r.position)
            }
        });
    } catch (error) {
        console.error('Error fetching filters:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to fetch filters',
            message: error.message
        });
    }
});

// Serve frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// For local development
if (process.env.AWS_EXECUTION_ENV === undefined) {
    app.listen(PORT, () => {
        console.log(`🚀 Server running on http://localhost:${PORT}`);
        console.log(`📊 API available at http://localhost:${PORT}/api/tires`);
    });
}

// Export for Lambda
module.exports.handler = serverless(app);
