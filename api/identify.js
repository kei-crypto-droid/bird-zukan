const ALLOWED_ORIGINS = ['*'];

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0]);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'POST only' });
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'OPENAI_API_KEY is not configured on the server.' });
  }

  const body = req.body || {};
  const image = typeof body.image === 'string' ? body.image : '';

  if (!image || !/^data:image\/(jpeg|jpg|png|webp);base64,/i.test(image)) {
    return res.status(400).json({ error: 'A base64 image data URL is required.' });
  }

  // Keep the image payload within a reasonable request size.
  if (image.length > 12_000_000) {
    return res.status(413).json({ error: 'Image is too large. Please choose a smaller photo.' });
  }

  const prompt = `あなたは日本の野鳥観察を支援する画像識別AIです。\nこの写真に写っている生物を識別してください。最優先は「鳥」です。白神山地と秋田県北部で観察される野鳥を前提に、日本語の標準和名で答えてください。\n\n判定ルール:\n- 鳥であることを確認してから種を推定する。\n- 写真だけでは種まで断定できない場合は、最も妥当な候補を選び、confidenceを低くする。\n- 種名を作り出さない。\n- 明らかに鳥でない場合は category を other または tree にする。\n- category は bird / other / tree のいずれか。\n- note は観察者向けに短く、写真から判断できる特徴だけを書く。\n- JSON以外の文字を返さない。\n\n次のJSON形式だけを返してください:\n{"species":"種名","category":"bird|other|tree","confidence":0.0,"note":"写真から分かる短い特徴"}`;

  try {
    const response = await fetch('https://api.openai.com/v1/responses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-5.6-luna',
        input: [
          {
            role: 'user',
            content: [
              { type: 'input_text', text: prompt },
              { type: 'input_image', image_url: image, detail: 'high' }
            ]
          }
        ],
        max_output_tokens: 180
      })
    });

    const raw = await response.text();
    if (!response.ok) {
      let detail = raw;
      try { detail = JSON.parse(raw)?.error?.message || raw; } catch (_) {}
      return res.status(response.status).json({ error: detail });
    }

    const data = JSON.parse(raw);
    const text = data.output_text || '';
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) {
      return res.status(502).json({ error: 'AI returned no JSON result.' });
    }

    const result = JSON.parse(match[0]);
    const category = ['bird', 'other', 'tree'].includes(result.category)
      ? result.category
      : 'bird';
    const confidence = Math.max(0, Math.min(1, Number(result.confidence) || 0));

    if (!result.species || typeof result.species !== 'string') {
      return res.status(502).json({ error: 'AI could not identify the image.' });
    }

    return res.status(200).json({
      species: result.species.trim(),
      category,
      confidence,
      note: typeof result.note === 'string' ? result.note.trim() : ''
    });
  } catch (error) {
    console.error('identify API error', error);
    return res.status(500).json({ error: 'AI identification request failed.' });
  }
}
