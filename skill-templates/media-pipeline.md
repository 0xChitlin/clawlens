# Media Pipeline Template

For multi-step content generation involving audio, video, images, or documents. Based on proven patterns from video-reels and content creation workflows.

## Template Files

### SKILL.md
```markdown
---
name: your-media-pipeline
description: Create media content through multi-step automation pipeline. Specify what type of content is generated and key use cases.
---

# Your Media Pipeline

Brief description of what this pipeline creates and when to use it.

## Critical Principles

Document the key lessons learned and non-obvious requirements:

1. **Audio-first design** — Generate audio first, then sync video to audio timing
2. **Measure before merge** — Never assume durations, always measure and validate
3. **Idempotent operations** — Pipeline should be resumable from any step
4. **Quality gates** — Validate output at each stage before proceeding
5. **Resource cleanup** — Clean up temporary files to prevent disk bloat

## Pipeline Overview

```
Input Data → Step 1 → Step 2 → Step 3 → Final Output
    ↓         ↓        ↓        ↓         ↓
  Validate   Audio    Video    Sync    Quality Check
```

## Quick Start

```bash
# Set provider/configuration
export PROVIDER=default

# Run full pipeline
./pipeline.sh <input_id> <source_directory>

# Run single step for debugging
./pipeline.sh <input_id> <source_directory> --step audio
```

## Requirements

List all dependencies:
- `ffmpeg` / `ffprobe` (media processing)
- `python3` (scripting)
- External services (TTS, image generation, etc.)
- Input file formats and naming conventions

## Pipeline Steps

### Step 1: Input Processing
- Validate input format and completeness
- Extract metadata and requirements
- Set up working directory structure

### Step 2: Content Generation
- Generate audio/video/image components
- Measure durations and dimensions
- Apply transformations and effects

### Step 3: Assembly
- Combine components with precise timing
- Add transitions, effects, overlays
- Generate multiple output formats if needed

### Step 4: Quality Assurance
- Validate output meets quality requirements
- Check file size, duration, format compliance
- Generate preview or test output

## Configuration

### Input Format

Document the expected input structure:

```json
{
  "id": "unique_identifier",
  "metadata": {
    "title": "Content title",
    "duration_target": 30,
    "format": "vertical"
  },
  "components": [
    {
      "type": "audio",
      "text": "Script for TTS generation",
      "voice": "preferred_voice"
    },
    {
      "type": "image", 
      "source": "image_path_or_url",
      "duration": 3.0
    }
  ]
}
```

### Provider Configuration

```bash
# TTS Provider options
export TTS_PROVIDER=elevenlabs  # elevenlabs|google|deepgram|local
export TTS_VOICE=default

# Quality settings
export OUTPUT_QUALITY=high      # low|medium|high
export OUTPUT_FORMAT=mp4        # mp4|mov|webm
```

## Quality Assurance

Before releasing output, validate:

- [ ] Audio quality (no artifacts, proper levels)
- [ ] Video sync (audio-video alignment within 0.1s)  
- [ ] File format (codec, container, metadata)
- [ ] Duration (within target range)
- [ ] File size (under platform limits)
- [ ] Accessibility (captions, descriptions if needed)

## Troubleshooting

### Common Issues

**Audio-video sync drift**
- Cause: Different rounding in audio vs video durations
- Solution: Use audio duration as source of truth, pad video to match

**Memory/disk usage**
- Cause: Large temporary files not cleaned up
- Solution: Stream processing where possible, clean temps after each step

**Quality degradation**
- Cause: Multiple re-encoding passes
- Solution: Keep intermediate files in lossless formats

### Debug Mode

```bash
# Enable detailed logging
export DEBUG=true
./pipeline.sh input_id source_dir

# Keep temporary files for inspection  
export KEEP_TEMPS=true
./pipeline.sh input_id source_dir
```

## Production Checklist

- [ ] All dependencies installed and tested
- [ ] Input validation catches common errors
- [ ] Error handling for external service failures
- [ ] Cleanup of temporary files
- [ ] Progress reporting for long operations
- [ ] Resumable from interruption
- [ ] Output quality verification
- [ ] Performance benchmarks documented
```

### pipeline.sh
```bash
#!/bin/bash
set -euo pipefail

# Main pipeline orchestrator
# Usage: ./pipeline.sh <input_id> <source_dir> [--step STEP]

input_id=${1?"Input ID required"}
source_dir=${2?"Source directory required"}
single_step=${3:-""}

# Configuration
export WORK_DIR="/tmp/pipeline_${input_id}_$$"
export DEBUG=${DEBUG:-false}
export KEEP_TEMPS=${KEEP_TEMPS:-false}

# Logging
log() {
  echo "[$(date '+%H:%M:%S')] $*" >&2
}

debug() {
  if [[ "$DEBUG" == "true" ]]; then
    echo "[DEBUG] $*" >&2
  fi
}

# Cleanup on exit
cleanup() {
  if [[ "$KEEP_TEMPS" != "true" ]]; then
    rm -rf "$WORK_DIR"
  else
    log "Temporary files kept in: $WORK_DIR"
  fi
}
trap cleanup EXIT

# Validation
validate_inputs() {
  log "Validating inputs..."
  
  if [[ ! -d "$source_dir" ]]; then
    echo "Error: Source directory not found: $source_dir" >&2
    exit 1
  fi
  
  local config_file="$source_dir/${input_id}.json"
  if [[ ! -f "$config_file" ]]; then
    echo "Error: Config file not found: $config_file" >&2
    exit 1
  fi
  
  # Validate JSON syntax
  if ! jq empty < "$config_file" 2>/dev/null; then
    echo "Error: Invalid JSON in config file" >&2
    exit 1
  fi
}

# Pipeline steps
step_generate_audio() {
  log "Generating audio components..."
  mkdir -p "$WORK_DIR/audio"
  
  # Extract text components and generate audio
  jq -r '.components[] | select(.type == "audio") | .text' "$source_dir/${input_id}.json" | \
  while IFS= read -r text; do
    # TTS generation logic here
    debug "Generating audio for: ${text:0:50}..."
    # Implementation depends on TTS provider
  done
}

step_process_video() {
  log "Processing video components..."
  mkdir -p "$WORK_DIR/video"
  
  # Process images, apply effects, create video segments
  # Implementation depends on media requirements
}

step_assemble() {
  log "Assembling final output..."
  
  # Combine audio and video with precise timing
  # Use ffmpeg to merge components
  local output_file="$WORK_DIR/${input_id}_final.mp4"
  
  # Quality validation before completion
  if validate_output "$output_file"; then
    cp "$output_file" "$source_dir/${input_id}_output.mp4"
    log "Pipeline complete: $source_dir/${input_id}_output.mp4"
  else
    echo "Error: Output failed quality validation" >&2
    exit 1
  fi
}

validate_output() {
  local file="$1"
  
  # Check file exists and is valid media
  if [[ ! -f "$file" ]] || ! ffprobe "$file" >/dev/null 2>&1; then
    return 1
  fi
  
  # Check duration, format, quality metrics
  local duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$file")
  debug "Output duration: $duration seconds"
  
  # Add specific quality checks here
  return 0
}

# Main execution
main() {
  log "Starting pipeline for: $input_id"
  
  validate_inputs
  mkdir -p "$WORK_DIR"
  
  # Run specific step or full pipeline
  case "${single_step}" in
    "--step audio") step_generate_audio ;;
    "--step video") step_process_video ;;
    "--step assemble") step_assemble ;;
    "")
      step_generate_audio
      step_process_video  
      step_assemble
      ;;
    *)
      echo "Unknown step: $single_step"
      exit 1
      ;;
  esac
}

main "$@"
```

### templates/input-template.json
```json
{
  "id": "example_001",
  "metadata": {
    "title": "Example Content",
    "description": "Template for pipeline input",
    "duration_target": 30,
    "output_format": "mp4",
    "resolution": "1080x1920"
  },
  "components": [
    {
      "type": "audio",
      "sequence": 1,
      "text": "Opening hook text for TTS generation",
      "voice": "default",
      "settings": {
        "speed": 1.0,
        "pitch": 0
      }
    },
    {
      "type": "image",
      "sequence": 2, 
      "source": "assets/slide1.png",
      "duration": 3.5,
      "effects": ["zoom", "fade"]
    }
  ],
  "output": {
    "filename": "example_001_final",
    "quality": "high",
    "target_size_mb": 50
  }
}
```

## Customization Checklist

- [ ] Define input/output formats for your specific media type
- [ ] Choose and configure media processing tools (ffmpeg, ImageMagick, etc.)
- [ ] Implement provider-specific API integrations (TTS, image generation)
- [ ] Add quality validation rules for your output requirements
- [ ] Create templates for common input configurations
- [ ] Add error recovery for external service failures
- [ ] Optimize for your target file sizes and formats
- [ ] Document hardware/software requirements

## Dependencies

- **Core**: `ffmpeg`, `ffprobe`, `jq`, `bash`
- **Media**: `ImageMagick` (image processing), `sox` (audio processing)  
- **APIs**: TTS service, image generation service (if applicable)
- **Storage**: Sufficient disk space for temporary files

## Performance Considerations

1. **Parallel Processing**: Run independent steps concurrently
2. **Streaming**: Process large files without loading entirely into memory
3. **Caching**: Cache expensive operations (TTS, image generation)
4. **Resource Limits**: Set memory and CPU limits for long-running processes
5. **Monitoring**: Track pipeline performance and bottlenecks