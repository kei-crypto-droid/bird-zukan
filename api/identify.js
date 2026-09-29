const path = require('path');
const express = require('express');

const app = express();
const PORT = process.env.PORT || 8080;

app.use(express.json({ limit: '15mb' }));

app.get('/health', (req, res) => {
  res.status(200).json({ ok: true, service: 'bird-zukan-api' });
});

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

app.options('*', (req, res) => {
  res.status(204).end();
});

app.post('/api/identify', async (req, res) => {
  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey) {
    return res.status(500).json({
      error: 'GEMINI_API_KEY is not configured on the server.'
    });
  }

  const body = req.body || {};
  const image = typeof body.image === 'string' ? body.image : '';

  if (!image || !/^data:image\/(jpeg|jpg|png|webp);base64,/i.test(image)) {
    return res.status(400).json({
      error: 'A base64 image data URL is required.'
    });
  }

  if (image.length > 12_000_000) {
    return res.status(413).json({
      error: 'Image is too large. Please choose a smaller photo.'
    });
  }

  const match = image.match(
    /^data:(image\/(?:jpeg|jpg|png|webp));base64,(.+)$/i
  );

  if (!match) {
    return res.status(400).json({
      error: 'Invalid image data.'
    });
  }

  const mimeType = match[1].toLowerCase();
  const base64Data = match[2];

  const prompt = `
あなたは日本の野鳥観察を支援する画像識別AIです。

この写真に写っている生物を識別してください。
最優先は「鳥」です。
白神山地と秋田県北部で観察される野鳥を前提に、
日本語の標準和名で答えてください。

判定ルール:
- まず鳥であることを確認する。
- 写真だけでは種まで断定できない場合は、最も妥当な候補を選び、confidenceを低くする。
- 存在しない種名を作らない。
- 明らかに鳥でない場合は category を other または tree にする。
- category は bird / other / tree のいずれか。
- note は観察者向けに短く、写真から判断できる特徴だけを書く。
- JSON以外の文字を返さない。

次の形式だけで返してください。

{
  "species": "種名",
  "category": "bird",
  "confidence": 0.0,
  "note": "写真から分かる短い特徴"
}
`;

  try {
    const response = await fetch(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': apiKey
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  inlineData: {
                    mimeType,
                    data: base64Data
                  }
                },
                {
                  text: prompt
                }
              ]
            }
          ],
          generationConfig: {
            responseMimeType: 'application/json',
            thinkingConfig: {
              thinkingLevel: 'low'
            }
          }
        })
      }
    );

    const raw = await response.text();

    if (!response.ok) {
      let detail = raw;

      try {
        detail = JSON.parse(raw)?.error?.message || raw;
      } catch (_) {}

      return res.status(response.status).json({
        error: detail
      });
    }

    const data = JSON.parse(raw);

    const text =
      data?.candidates?.[0]?.content?.parts?.[0]?.text || '';

    if (!text) {
      return res.status(502).json({
        error: 'Gemini returned no result.'
      });
    }

    const result = JSON.parse(text);

    const category =
      ['bird', 'other', 'tree'].includes(result.category)
        ? result.category
        : 'bird';

    const confidence = Math.max(
      0,
      Math.min(1, Number(result.confidence) || 0)
    );

    if (
      !result.species ||
      typeof result.species !== 'string'
    ) {
      return res.status(502).json({
        error: 'Gemini could not identify the image.'
      });
    }

    return res.status(200).json({
      species: result.species.trim(),
      category,
      confidence,
      note:
        typeof result.note === 'string'
          ? result.note.trim()
          : ''
    });

  } catch (error) {
    console.error('Gemini identification error:', error);

    return res.status(500).json({
      error: 'Gemini identification request failed.'
    });
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'shiratsuchi-fieldnote_chatgpt.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Bird Zukan API listening on port ${PORT}`);
});
