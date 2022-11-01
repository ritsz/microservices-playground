package envoy.authz

import future.keywords.if
import future.keywords.in

default allow := false

allow if {
    is_post
    is_files
    "file-uploader" in claims.perms
}

allow if {
    not is_post
    is_files
    "data-reader" in claims.perms
}

allow if {
    not is_post
    is_analysis
    "data-reader" in claims.perms
}

is_post if input.attributes.request.http.method == "POST"

is_files := true if {
    contains(input.attributes.request.http.path, "/v1/api/files")
}

is_analysis := true if {
    contains(input.attributes.request.http.path, "/v1/api/analysis")
}

claims := payload if {
    [_, payload, _] := io.jwt.decode(bearer_token)
}

default bearer_token := ""
bearer_token := t if {
    v := input.attributes.request.http.headers.authorization
    startswith(v, "Bearer ")
    t := substring(v, count("Bearer "), -1)
}
