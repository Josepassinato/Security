# Vimeo Upload Notes

Status: pending credentials.

The CARD-016 video package is ready for Vimeo upload, but this environment does not have a Vimeo login session or upload API token.

Recommended Vimeo settings:

- Privacy: unlisted or private link.
- Downloads: disabled unless the recipient explicitly needs offline access.
- Search indexing: disabled.
- Comments: disabled.
- Embed: disabled or restricted to approved domains.
- Title: `Quarry - 5 Minute Autonomous Threat Hunting Demo`
- Description: `Confidential demo package. Synthetic data only. No customer data.`

Files to upload:

- Full version: `docs/pitch/videos/quarry-demo-5min.mp4`
- Optional teaser: `docs/pitch/videos/quarry-demo-2min-teaser.mp4`
- Optional social cut: `docs/pitch/videos/quarry-demo-30s-social.mp4`

Caption sidecars:

- English: `docs/pitch/videos/quarry-demo-5min.en.srt`
- Portuguese: `docs/pitch/videos/quarry-demo-5min.pt-br.srt`

After upload, add the Vimeo URL to:

- `docs/pitch/videos/manifest.json`
- `docs/pitch/letter-to-cofounder.md`
- `docs/pitch/email-to-cofounder-template.md`
