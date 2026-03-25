const express = require("express");
const pool = require("../db");

const router = express.Router();

router.post("/", async (req, res) => {
  try {
    const { zone, person_count, risk_level, prediction } = req.body;

    const [result] = await pool.execute(
      "INSERT INTO crowd_data (zone, person_count, risk_level, prediction) VALUES (?, ?, ?, ?)",
      [zone, person_count, risk_level, prediction]
    );

    res.status(201).json({
      id: result.insertId,
      zone,
      person_count,
      risk_level,
      prediction,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/", async (req, res) => {
  try {
    const [rows] = await pool.execute(
      "SELECT * FROM crowd_data ORDER BY created_at DESC LIMIT 50"
    );
    res.json(rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/zones/latest", async (req, res) => {
  try {
    const [rows] = await pool.execute(`
      SELECT c1.*
      FROM crowd_data c1
      INNER JOIN (
        SELECT zone, MAX(created_at) AS latest_time
        FROM crowd_data
        GROUP BY zone
      ) c2
      ON c1.zone = c2.zone AND c1.created_at = c2.latest_time
      ORDER BY c1.created_at DESC
    `);

    res.json(rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;