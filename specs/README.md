# Specs

The binding rules of gangway. One file holds one rule. The rules for specs are in
[style/specs/](style/specs/). Copy [TEMPLATE.md](TEMPLATE.md) to start a new rule.

## Tree

```
specs/
  style/
    backend/   animations, python
    frontend/  angular
    shared/    git, testing, tooling, writing
    specs/     content, format, structure
  requirements/
    functional/
      audio/          analysis, capture, settings
      configuration/  config-api, config-file
      lighting/       animation-config, layout, meta-animations, render
      live/           data
      presets/        library
      sensor/         events, statistics
      web-ui/         access, editor, navigation
    non-functional/
      compatibility/  deploy, hardware
      security/       access, secrets, sensor
```

The second level is the area, the third level is the topic. A topic folder holds the rule
files, for example `requirements/functional/presets/library/000058_preset-in-use.md`.

Check the specs with `python3 scripts/check_specs.py`. Write the tree and the index again with
`python3 scripts/check_specs.py --write`.

## Index

| ID | Title | Status |
| --- | --- | --- |
| [F/audio/analysis/000081](requirements/functional/audio/analysis/000081_noise-floor.md) | Sound below the noise floor is silence | approved |
| [F/audio/analysis/000082](requirements/functional/audio/analysis/000082_bass-gain.md) | The bass gain scales only the bass bands | approved |
| [F/audio/analysis/000083](requirements/functional/audio/analysis/000083_tempo-beats.md) | A tempo needs four beats in eight seconds | approved |
| [F/audio/analysis/000084](requirements/functional/audio/analysis/000084_beat-grid.md) | Beats lie on a tempo grid | approved |
| [F/audio/analysis/000085](requirements/functional/audio/analysis/000085_animation-clock.md) | Beat times use the animation clock | approved |
| [F/audio/capture/000075](requirements/functional/audio/capture/000075_child-process.md) | The microphone runs in a child process | approved |
| [F/audio/capture/000076](requirements/functional/audio/capture/000076_error-retry.md) | A capture error gives silence and a retry | approved |
| [F/audio/capture/000077](requirements/functional/audio/capture/000077_disabled.md) | A disabled capture does not open the microphone | approved |
| [F/audio/capture/000078](requirements/functional/audio/capture/000078_direct-device.md) | The capture prefers the direct hardware device | approved |
| [F/audio/settings/000079](requirements/functional/audio/settings/000079_defaults.md) | A missing audio setting gives its default | approved |
| [F/audio/settings/000080](requirements/functional/audio/settings/000080_invalid.md) | An invalid audio setting is refused | approved |
| [F/configuration/config-api/000059](requirements/functional/configuration/config-api/000059_only-animation.md) | The config API changes only the animation | approved |
| [F/configuration/config-api/000060](requirements/functional/configuration/config-api/000060_no-audio-section.md) | A config file without an audio section keeps none | approved |
| [F/configuration/config-file/000061](requirements/functional/configuration/config-file/000061_config-path.md) | GANGWAY_CONFIG names the config file | approved |
| [F/lighting/animation-config/000045](requirements/functional/lighting/animation-config/000045_one-function.md) | An animation config names one function | approved |
| [F/lighting/animation-config/000046](requirements/functional/lighting/animation-config/000046_unknown-names.md) | An unknown function or parameter is refused | approved |
| [F/lighting/animation-config/000047](requirements/functional/lighting/animation-config/000047_variadic-list.md) | A variadic parameter takes a list | approved |
| [F/lighting/animation-config/000048](requirements/functional/lighting/animation-config/000048_times-stay-strings.md) | Times of day stay strings in YAML | approved |
| [F/lighting/layout/000041](requirements/functional/lighting/layout/000041_led-positions.md) | LED positions follow the strips | approved |
| [F/lighting/meta-animations/000049](requirements/functional/lighting/meta-animations/000049_schedule-past-midnight.md) | A schedule window can go past midnight | approved |
| [F/lighting/meta-animations/000050](requirements/functional/lighting/meta-animations/000050_schedule-default.md) | An invalid schedule window uses 18:00 to 06:00 | approved |
| [F/lighting/meta-animations/000051](requirements/functional/lighting/meta-animations/000051_missing-preset-off.md) | A missing or recursive preset turns the LEDs off | approved |
| [F/lighting/render/000042](requirements/functional/lighting/render/000042_one-frame-context.md) | All LEDs of a frame get the same time and context | approved |
| [F/lighting/render/000043](requirements/functional/lighting/render/000043_reload-without-restart.md) | A new animation applies without a restart | approved |
| [F/lighting/render/000044](requirements/functional/lighting/render/000044_frame-rate.md) | The frame rate is the mean of the last 100 frames | approved |
| [F/live/data/000086](requirements/functional/live/data/000086_audio-silence.md) | The audio data is silent without a capture | approved |
| [F/live/data/000087](requirements/functional/live/data/000087_before-start.md) | Live data is empty before the controller starts | approved |
| [F/presets/library/000052](requirements/functional/presets/library/000052_files-next-to-config.md) | Presets are YAML files next to the config | approved |
| [F/presets/library/000053](requirements/functional/presets/library/000053_safe-name.md) | A preset name uses only safe characters | approved |
| [F/presets/library/000054](requirements/functional/presets/library/000054_save-active.md) | A save without a body stores the active animation | approved |
| [F/presets/library/000055](requirements/functional/presets/library/000055_load-preset.md) | A loaded preset becomes the active animation | approved |
| [F/presets/library/000056](requirements/functional/presets/library/000056_rename-references.md) | A rename updates every reference | approved |
| [F/presets/library/000057](requirements/functional/presets/library/000057_shipped-presets.md) | Every shipped preset loads and renders | approved |
| [F/presets/library/000058](requirements/functional/presets/library/000058_preset-in-use.md) | A preset in use cannot be deleted | approved |
| [F/sensor/events/000062](requirements/functional/sensor/events/000062_receiver.md) | The sensor events arrive on port 8081 | approved |
| [F/sensor/events/000063](requirements/functional/sensor/events/000063_skip-invalid.md) | An invalid event item is skipped | approved |
| [F/sensor/events/000064](requirements/functional/sensor/events/000064_delete-track.md) | A track deletion removes the person | approved |
| [F/sensor/events/000065](requirements/functional/sensor/events/000065_older-event.md) | An older event does not move a person | approved |
| [F/sensor/events/000066](requirements/functional/sensor/events/000066_floor-projection.md) | Positions are projected to the floor | approved |
| [F/sensor/statistics/000067](requirements/functional/sensor/statistics/000067_count-line.md) | The counts come from count line 0 | approved |
| [F/sensor/statistics/000068](requirements/functional/sensor/statistics/000068_occupancy-morning.md) | The occupancy starts at zero at 04:00 | approved |
| [F/sensor/statistics/000069](requirements/functional/sensor/statistics/000069_occupancy-not-negative.md) | The occupancy is never below zero | approved |
| [F/sensor/statistics/000070](requirements/functional/sensor/statistics/000070_count-ranges.md) | The count ranges are day, week and month | approved |
| [F/sensor/statistics/000071](requirements/functional/sensor/statistics/000071_local-time.md) | Days and weeks use the local timezone | approved |
| [F/sensor/statistics/000072](requirements/functional/sensor/statistics/000072_sensor-cache.md) | Sensor answers are cached | approved |
| [F/sensor/statistics/000073](requirements/functional/sensor/statistics/000073_unreachable-502.md) | An unreachable sensor gives 502 | approved |
| [F/sensor/statistics/000074](requirements/functional/sensor/statistics/000074_heatmap-crop.md) | The heat map is cropped to its picture | approved |
| [F/web-ui/access/000088](requirements/functional/web-ui/access/000088_no-key-first.md) | The web UI sends no key first | approved |
| [F/web-ui/access/000089](requirements/functional/web-ui/access/000089_key-prompt.md) | A refused key opens the key prompt | approved |
| [F/web-ui/access/000090](requirements/functional/web-ui/access/000090_key-in-link.md) | A key in the link is stored and removed from the address | approved |
| [F/web-ui/editor/000092](requirements/functional/web-ui/editor/000092_schema-driven.md) | The editor builds its form from the animation schema | approved |
| [F/web-ui/editor/000093](requirements/functional/web-ui/editor/000093_cleared-number.md) | A cleared number uses the backend default | approved |
| [F/web-ui/navigation/000091](requirements/functional/web-ui/navigation/000091_legacy-hashes.md) | Old hash links go to the new routes | approved |
| [NF/compatibility/deploy/000099](requirements/non-functional/compatibility/deploy/000099_state-folder.md) | The app state lives in /var/lib/gangway | approved |
| [NF/compatibility/hardware/000098](requirements/non-functional/compatibility/hardware/000098_pwm0.md) | The LED data line uses PWM0 on GPIO 18 | approved |
| [NF/security/access/000094](requirements/non-functional/security/access/000094_api-key.md) | Every API route needs the API key | approved |
| [NF/security/access/000095](requirements/non-functional/security/access/000095_no-server-key.md) | The API refuses requests without a server key | approved |
| [NF/security/secrets/000097](requirements/non-functional/security/secrets/000097_sops.md) | Secrets are encrypted with sops | approved |
| [NF/security/sensor/000096](requirements/non-functional/security/sensor/000096_read-only-paths.md) | The sensor client reads only fixed read-only paths | approved |
| [S/backend/animations/000035](style/backend/animations/000035_export-in-all.md) | An animation is exported by its package | approved |
| [S/backend/animations/000036](style/backend/animations/000036_signature.md) | An animation is a function of time, context, LED and persons | approved |
| [S/backend/animations/000037](style/backend/animations/000037_frame-values-once.md) | An audio animation computes frame values once | approved |
| [S/backend/python/000033](style/backend/python/000033_strict-checks.md) | Python code passes ruff and strict basedpyright | approved |
| [S/backend/python/000034](style/backend/python/000034_google-docstrings.md) | Docstrings use the Google convention | approved |
| [S/frontend/angular/000038](style/frontend/angular/000038_kit-components.md) | The frontend uses the kit components and the semantic tokens | approved |
| [S/frontend/angular/000039](style/frontend/angular/000039_standalone-signals.md) | Components are standalone with signals and OnPush | approved |
| [S/frontend/angular/000040](style/frontend/angular/000040_frontend-checks.md) | A frontend change passes build, test and lint | approved |
| [S/shared/git/000032](style/shared/git/000032_ui-kit-pin.md) | The ui-kit flake input has the commit of the submodule | approved |
| [S/shared/testing/000030](style/shared/testing/000030_test-refers-to-rule.md) | A test refers back to its rule | approved |
| [S/shared/testing/000031](style/shared/testing/000031_synthetic-signals.md) | The sound analysis is tested with synthetic signals | approved |
| [S/shared/tooling/000027](style/shared/tooling/000027_nix-dev-shell.md) | Commands run in the Nix dev shell | approved |
| [S/shared/writing/000028](style/shared/writing/000028_ste-english.md) | Repository texts are written in STE English | approved |
| [S/shared/writing/000029](style/shared/writing/000029_true-docstrings.md) | A docstring is true | approved |
| [S/specs/content/000015](style/specs/content/000015_only-the-rule.md) | A spec contains only the rule | approved |
| [S/specs/content/000016](style/specs/content/000016_one-thing.md) | One rule controls one thing | approved |
| [S/specs/content/000017](style/specs/content/000017_examinable.md) | A rule can be examined | approved |
| [S/specs/content/000018](style/specs/content/000018_must-and-must-not.md) | The rule text uses must and must not | approved |
| [S/specs/content/000019](style/specs/content/000019_reason.md) | A rule gives its reason | approved |
| [S/specs/content/000020](style/specs/content/000020_test.md) | A rule names its test | approved |
| [S/specs/content/000021](style/specs/content/000021_current-rule.md) | A spec states the current rule | approved |
| [S/specs/content/000022](style/specs/content/000022_ste.md) | A spec is written in ASD-STE100 | approved |
| [S/specs/content/000023](style/specs/content/000023_product-terms.md) | Product terms stay as the UI and the config show them | approved |
| [S/specs/format/000001](style/specs/format/000001_copy-the-template.md) | A new spec starts as a copy of the template | approved |
| [S/specs/format/000002](style/specs/format/000002_front-matter.md) | A spec starts with a YAML front matter | approved |
| [S/specs/format/000003](style/specs/format/000003_status.md) | The status shows the approval | approved |
| [S/specs/format/000004](style/specs/format/000004_one-rule-per-file.md) | One file holds one rule | approved |
| [S/specs/format/000005](style/specs/format/000005_rule-id.md) | The rule ID has kind, path and number | approved |
| [S/specs/format/000006](style/specs/format/000006_unique-number.md) | The number is the identity of a rule | approved |
| [S/specs/format/000007](style/specs/format/000007_moved-rule.md) | A moved rule keeps its number | approved |
| [S/specs/format/000008](style/specs/format/000008_labels.md) | Labels in a rule are fixed | approved |
| [S/specs/format/000024](style/specs/format/000024_section-sign-reference.md) | Code refers to a rule with the § sign | approved |
| [S/specs/format/000025](style/specs/format/000025_file-name.md) | The file name is number and name | approved |
| [S/specs/structure/000009](style/specs/structure/000009_precedence.md) | A spec wins over other guidance | approved |
| [S/specs/structure/000010](style/specs/structure/000010_tree.md) | The tree sorts by kind, then by area and topic | approved |
| [S/specs/structure/000011](style/specs/structure/000011_folder-names.md) | Folder names are lower case kebab case | approved |
| [S/specs/structure/000012](style/specs/structure/000012_one-place.md) | A rule is written in one place | approved |
| [S/specs/structure/000013](style/specs/structure/000013_index.md) | The index lists every rule | approved |
| [S/specs/structure/000014](style/specs/structure/000014_change-process.md) | A change goes through a pull request | approved |
| [S/specs/structure/000026](style/specs/structure/000026_spec-first.md) | A change request starts as a spec | approved |
