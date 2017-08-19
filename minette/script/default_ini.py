; -----------------------------------------------------------------------------
; Minette configuration file
; -----------------------------------------------------------------------------

; FORMAT
; -----------------
; key = value
; -----------------

; using OS environment variables (e.g. to get the value of "os_env_key" from system env)
; -----------------
; key = ENV::os_env_key
; -----------------

[minette]
; Timezone
timezone = ENV::MINETTE_TIMEZONE

; Connection strings
connection_str = ENV::MINETTE_CONSTR

; Default Classifier
default_classifier = ENV::MINETTE_DEFAULT_CLASSIFIER

; Default DialogService
default_dialog_service = ENV::MINETTE_DEFAULT_DIALOG_SERVICE

; Chatting
chatting_api_key = ENV::CHAT_API_KEY

; Google API Key
google_api_key = ENV::GOOGLE_API_KEY

[line_bot_api]
channel_secret = ENV::LINE_CHANNEL_SECRET
channel_access_token = ENV::LINE_ACCESS_TOKEN
