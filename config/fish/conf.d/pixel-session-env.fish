# Recover missing session variables only when the current user's sockets exist.
if not set -q XDG_RUNTIME_DIR
    set -l runtime /run/user/(id -u)
    if test -d $runtime; and test -O $runtime
        set -gx XDG_RUNTIME_DIR $runtime
    end
end
if not set -q DBUS_SESSION_BUS_ADDRESS; and set -q XDG_RUNTIME_DIR
    if test -S "$XDG_RUNTIME_DIR/bus"
        set -gx DBUS_SESSION_BUS_ADDRESS "unix:path=$XDG_RUNTIME_DIR/bus"
    end
end
