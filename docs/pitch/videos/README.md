# Quarry Demo Video Package

Generated for CARD-016.

## Final video files

- `quarry-demo-5min.mp4` - full 5-minute narrated version with English captions burned in.
- `quarry-demo-2min-teaser.mp4` - 2-minute teaser cut from the full version.
- `quarry-demo-30s-social.mp4` - 30-second social cut from the full version.

## Caption files

- `quarry-demo-5min.en.srt`
- `quarry-demo-5min.pt-br.srt`

The full video has English captions burned in. The PT-BR SRT is provided as the Portuguese caption version.

## Audio and music

Narration uses a generated English voiceover for the async demo package. Replace with human studio narration before a high-stakes external launch if desired.

The background music bed is generated in-house with ffmpeg sine synthesis inside `scripts/generate_demo_video_card016.py`. It uses no third-party samples, so there is no external music license dependency.

## Vimeo hosting

Vimeo upload is not completed because the environment does not have Vimeo credentials or a configured upload token. Recommended upload mode: Vimeo unlisted/private link, downloads disabled, no public search indexing.

## Privacy controls

- No real customer data.
- No third-party company logos.
- Demo credentials are not embedded in the video or captions.
