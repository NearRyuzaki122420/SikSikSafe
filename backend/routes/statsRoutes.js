const express = require("express");
const pool = require("../db");

const router = express.Router();

router.get("/summary", async (req, res) => {
  try {
    const [[totalZones]] = await pool.execute(
      "SELECT COUNT(DISTINCT zone) AS total_zones FROM crowd_data"
    );

    const [[highRisk]] = await pool.execute(
      "SELECT COUNT(*) AS high_risk_count FROM crowd_data WHERE risk_level = 'HIGH'"
    );

    const [[latestPeople]] = await pool.execute(
      "SELECT COALESCE(SUM(person_count), 0) AS total_people FROM (" +
      "SELECT zone, person_count FROM crowd_data cd1 " +
      "WHERE created_at = (" +
      "SELECT MAX(cd2.created_at) FROM crowd_data cd2 WHERE cd2.zone = cd1.zone" +
      ")) latest_zone_data"
    );

    const [[latestAlert]] = await pool.execute(
      "SELECT zone, risk_level, prediction, created_at FROM crowd_data ORDER BY created_at DESC LIMIT 1"
    );

    res.json({
      total_zones: totalZones.total_zones || 0,
      high_risk_count: highRisk.high_risk_count || 0,
      total_people: latestPeople.total_people || 0,
      latest_alert: latestAlert || null,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/risk-counts", async (req, res) => {
  try {
    const [rows] = await pool.execute(`
      SELECT risk_level, COUNT(*) AS count
      FROM crowd_data
      GROUP BY risk_level
    `);

    const result = {
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
    };

    rows.forEach((row) => {
      result[row.risk_level] = row.count;
    });

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;