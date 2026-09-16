# Migration from sports-betting-prediction-expert

The canonical skill and plugin identifier is now `sports-betting-expert`. Existing prompts that explicitly invoke `$sports-betting-prediction-expert` should use `$sports-betting-expert` after installing v1.0.0. Domain behavior was merged into the new canonical skill; no legacy alias is installed because duplicate skill descriptions would make automatic selection less predictable.

