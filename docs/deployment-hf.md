# Hugging Face Spaces デプロイガイド

詳細は `/home/driller/work/agent-leaderboard/plans/multi-platform-deployment.md` のPhase 5を参照してください。

## クイックスタート

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/agent-leaderboard
git push hf main
```

環境変数をSettings → Repository secretsで設定：
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`
- `HF_TOKEN`
