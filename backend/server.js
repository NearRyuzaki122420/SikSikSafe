const express = require("express");
const http = require("http");
const cors = require("cors");
const { Server } = require("socket.io");
const pool = require("./db");
require("dotenv").config();

const authRoutes = require("./routes/authRoutes");
const crowdRoutes = require("./routes/crowdRoutes");
const statsRoutes = require("./routes/statsRoutes");

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: "*",
  },
});

app.use(cors());
app.use(express.json());

app.get("/", async (req, res) => {
  try {
    await pool.execute("SELECT 1");
    res.send("SikSikSafe backend with MySQL is running");
  } catch (error) {
    res.status(500).send("Database connection failed");
  }
});

app.use("/api/auth", authRoutes);
app.use("/api/crowd-data", crowdRoutes);
app.use("/api/stats", statsRoutes);

app.post("/api/live-crowd-data", async (req, res) => {
  try {
    const { zone, person_count, risk_level, prediction } = req.body;

    const [result] = await pool.execute(
      "INSERT INTO crowd_data (zone, person_count, risk_level, prediction) VALUES (?, ?, ?, ?)",
      [zone, person_count, risk_level, prediction]
    );

    const liveData = {
      id: result.insertId,
      zone,
      person_count,
      risk_level,
      prediction,
    };

    io.emit("crowdUpdate", liveData);

    if (risk_level === "HIGH") {
      io.emit("alert", {
        message: `High risk detected in ${zone}`,
        zone,
        risk_level,
      });
    }

    res.status(201).json(liveData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

io.on("connection", (socket) => {
  console.log("Client connected");
});

const PORT = process.env.PORT || 5000;

server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});