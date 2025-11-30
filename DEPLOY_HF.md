# 🚀 Deploy CodeAtlas to HuggingFace Space

Complete step-by-step guide to deploy CodeAtlas to the MCP-1st-Birthday HuggingFace Space for hackathon submission.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] HuggingFace account
- [ ] Access to `MCP-1st-Birthday` organization (request if needed)
- [ ] Demo video recorded and uploaded to GitHub
- [ ] Social media post published (X/Twitter) — **REQUIRED by hackathon**
- [ ] README.md updated with actual video and social post links
- [ ] All code committed to GitHub

---

## Step 1: Install HuggingFace CLI

```bash
pip install huggingface_hub
```

---

## Step 2: Login to HuggingFace

```bash
huggingface-cli login
```

When prompted:
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with **Write** access
3. Paste the token in terminal

---

## Step 3: Create the HuggingFace Space

1. Go to https://huggingface.co/new-space
2. **Owner:** Select `MCP-1st-Birthday` organization
3. **Space name:** `CodeAtlas`
4. **License:** MIT
5. **SDK:** Gradio
6. **Hardware:** CPU Basic (free tier is fine)
7. Click **Create Space**

---

## Step 4: Clone Your GitHub Repo (if not already)

```bash
# If starting fresh
git clone https://github.com/aghilsabu/codeAtlas.git
cd codeAtlas
```

---

## Step 5: Add HuggingFace Space as Git Remote

```bash
# Add HF Space as a second remote
git remote add hf https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas

# Verify remotes
git remote -v
# Should show:
# origin  https://github.com/aghilsabu/codeAtlas.git (fetch/push)
# hf      https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas (fetch/push)
```

---

## Step 6: Update README with Real Links

Before pushing, update these placeholders in `README.md`:

### Demo Video
Replace this line:
```
https://github.com/user-attachments/assets/YOUR_VIDEO_ID
```
With your actual GitHub video URL (upload video to a GitHub issue/PR to get the link).

### Social Media Post
Replace this link:
```
https://x.com/your-post-link
```
With your actual X/Twitter post URL. **This is REQUIRED by hackathon rules!**

---

## Step 7: Commit All Changes

```bash
# Stage all changes
git add -A

# Commit
git commit -m "Final hackathon submission - CodeAtlas"

# Push to GitHub first (backup)
git push origin main
```

---

## Step 8: Push to HuggingFace Space

```bash
# Push to HF Space (this triggers deployment)
git push hf main
```

If you get authentication errors:
```bash
# Use token-based URL
git remote set-url hf https://<YOUR_HF_USERNAME>:<YOUR_HF_TOKEN>@huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas
git push hf main
```

---

## Step 9: Configure Secrets on HuggingFace

Go to: **https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/settings**

Scroll to **"Repository secrets"** and add:

| Secret Name | Required | How to Get |
|-------------|----------|------------|
| `GEMINI_API_KEY` | ✅ **Yes** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | Optional | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ELEVENLABS_API_KEY` | Optional | [elevenlabs.io/app/developers](https://elevenlabs.io/app/developers/api-keys) |

⚠️ **Without GEMINI_API_KEY, the app won't work!**

---

## Step 10: Wait for Build & Verify

1. **Watch the build:** https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/logs
2. Build takes ~2-5 minutes
3. Once "Running" appears, test the app

### Test Checklist

- [ ] App loads at https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas
- [ ] Can analyze a GitHub repo (try: `https://github.com/gradio-app/gradio`)
- [ ] Diagram generates correctly
- [ ] Voice narration works (if ElevenLabs key added)
- [ ] MCP endpoint responds: https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/gradio_api/mcp/sse

---

## 🔧 Troubleshooting

### Build Fails
```bash
# Check logs at:
https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/logs
```
Common issues:
- Missing dependency in `requirements.txt`
- Python version mismatch
- Import errors

### App Crashes on Startup
- Verify `GEMINI_API_KEY` secret is set
- Check that `app.py` exists in root directory
- Look for import errors in logs

### "No Space Disk Space"
- Go to Settings → Factory Reboot
- Or delete old files from `data/` folder

### MCP Endpoint Not Working
- Ensure `mcp_server=True` in `demo.launch()`
- Test SSE endpoint directly in browser
- Check that Gradio version is 5.x+

### Permission Denied on Push
```bash
# Re-authenticate
huggingface-cli login

# Or use token in URL
git remote set-url hf https://YOUR_USERNAME:YOUR_TOKEN@huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas
```

---

## 📝 Hackathon Submission Requirements

Per hackathon rules, ensure your submission has:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Submitted to `MCP-1st-Birthday` org | ⬜ | Must push to org Space, not personal |
| Track tag in README | ✅ | `mcp-in-action-track-consumer` |
| Social media post link | ⬜ | **REQUIRED** - Update README |
| Demo video | ⬜ | Recommended - Update README |
| Original work (Nov 14-30) | ✅ | Must be created during hackathon |

---

## 🔗 Quick Reference Links

| Resource | URL |
|----------|-----|
| **Live App** | https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas |
| **MCP SSE Endpoint** | https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/gradio_api/mcp/sse |
| **Space Settings** | https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/settings |
| **Build Logs** | https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/logs |
| **Hackathon Page** | https://huggingface.co/MCP-1st-Birthday |
| **HF Tokens** | https://huggingface.co/settings/tokens |

---

## ⚡ Quick Deploy Commands (TL;DR)

```bash
# One-time setup
pip install huggingface_hub
huggingface-cli login
git remote add hf https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas

# Deploy
git add -A && git commit -m "Deploy to HF"
git push origin main  # Backup to GitHub
git push hf main      # Deploy to HF Space

# Then add secrets at:
# https://huggingface.co/spaces/MCP-1st-Birthday/CodeAtlas/settings
```

---

**Deadline: November 30, 2025, 11:59 PM UTC** ⏰

Good luck! 🎉
