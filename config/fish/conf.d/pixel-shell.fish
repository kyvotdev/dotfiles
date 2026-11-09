if status is-interactive
    set -g fish_greeting
    fish_add_path $HOME/.local/bin
    set -gx STARSHIP_CONFIG $HOME/.config/starship.toml
    if type -q starship
        starship init fish | source
    end
    function __pixel_colors --on-event fish_prompt
        source $HOME/.config/pixel-shell/colors.fish
    end
    source $HOME/.config/pixel-shell/colors.fish
    abbr -a ll 'ls -lah'
    abbr -a wifi 'pixel-control wifi'
    abbr -a bt 'pixel-bluetooth'
    abbr -a hotspot 'pixel-control hotspot'
    abbr -a theme 'pixel-theme'
    if type -q zoxide
        zoxide init fish | source
    end
end
