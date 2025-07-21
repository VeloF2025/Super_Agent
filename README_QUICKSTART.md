# 🚀 Jarvis Super Agent - Get Started in 60 Seconds

## The Fastest Way to Start (Choose One)

### Option 1: One-Command Setup (Recommended)
```bash
curl -sSL https://get.jarvis.ai | bash
```
*This single command downloads, installs, and starts everything!*

### Option 2: Quick Local Setup
```bash
git clone https://github.com/yourusername/jarvis-super-agent
cd jarvis-super-agent
chmod +x quickstart.sh
./quickstart.sh
```

### Option 3: Docker (Cleanest)
```bash
git clone https://github.com/yourusername/jarvis-super-agent
cd jarvis-super-agent
docker-compose up
```

That's it! Jarvis is now running at http://localhost:3000 🎉

---

## 🎯 What Just Happened?

You now have:
- ✅ **5 AI Agents** ready to work for you
- ✅ **Beautiful Dashboard** to control everything  
- ✅ **ML Optimization** learning and improving
- ✅ **Your First Project** already created

## 🎮 Your First 5 Minutes

### 1. Open the Dashboard
Go to http://localhost:3000 - it should open automatically

### 2. See Your AI Agents
Click on "Agents" in the sidebar to see your team:
- 🧠 **Orchestrator** - The team leader
- 🏗️ **Architect** - System designer
- 🔬 **Researcher** - Information gatherer
- ✅ **Quality** - Code reviewer
- 📢 **Communicator** - Status reporter

### 3. Create Your First Task
1. Click "Dashboard"
2. Click "New Task" button
3. Type: "Create a simple web app"
4. Hit Enter
5. Watch the agents collaborate!

### 4. Explore ML Insights
Click "ML Optimization" to see:
- How agents are performing
- Who works best together
- System learning in real-time

---

## 🛠️ Common Commands

### Start/Stop
```bash
# Start Jarvis
./start-jarvis.sh     # or docker-compose up

# Stop Jarvis  
Ctrl+C               # or docker-compose down
```

### Create a Task via API
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Build a REST API"}'
```

### Check Agent Status
```bash
curl http://localhost:8000/api/agents/status
```

---

## 📁 What's in the Box?

```
jarvis/
├── 🎯 quickstart.sh      # One-click setup
├── 🎨 agent-dashboard/   # Beautiful web interface
├── 🧠 memory/           # AI learning & memory
├── 📂 projects/         # Your projects go here
├── 🤖 agents/           # Agent definitions
└── 📊 logs/             # System logs
```

---

## 🔧 Configuration (Optional)

### Add Your API Keys
Edit `.env` file:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Change Ports
```env
DASHBOARD_PORT=3000
API_PORT=8000
```

### Add More Agents
```env
AGENT_COUNT=10
```

---

## 🚨 Troubleshooting

### Nothing happens when I run quickstart?
```bash
# Make sure it's executable
chmod +x quickstart.sh

# Try with bash explicitly
bash quickstart.sh
```

### Port already in use?
```bash
# Change ports in .env file
DASHBOARD_PORT=3001
API_PORT=8001
```

### Agents not responding?
```bash
# Restart services
docker-compose restart  # or ./start-jarvis.sh
```

---

## 🎓 Next Steps

1. **Read the Tutorial**
   ```bash
   python tutorial.py
   ```

2. **Join the Community**
   - Discord: https://discord.gg/jarvis-ai
   - Forum: https://community.jarvis.ai

3. **Watch the Video Tutorial**
   - https://youtube.com/jarvis-quickstart

4. **Explore Advanced Features**
   - [ML Optimization Guide](./docs/ml-optimization.md)
   - [Agent Customization](./docs/agents.md)
   - [API Reference](http://localhost:8000/docs)

---

## 💡 Pro Tips

- **Keyboard Shortcuts**: Press `?` in the dashboard for shortcuts
- **Dark Mode**: Click the moon icon in the top right
- **Export Data**: Use the API endpoint `/api/export`
- **Bulk Tasks**: Drag and drop a CSV file into the dashboard

---

## 🆘 Need Help?

- **Quick Help**: Run `jarvis help`
- **Docs**: https://docs.jarvis.ai
- **Issues**: https://github.com/yourusername/jarvis/issues
- **Email**: support@jarvis.ai

---

**That's it! You're ready to build amazing things with AI agents. Have fun! 🚀**