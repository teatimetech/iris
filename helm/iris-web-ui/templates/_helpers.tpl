{{- define "iris-web-ui.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "iris-web-ui.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "iris-web-ui.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "iris-web-ui.labels" -}}
helm.sh/chart: {{ include "iris-web-ui.chart" . }}
{{ include "iris-web-ui.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "iris-web-ui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "iris-web-ui.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: iris-web-ui
{{- end }}

{{- define "iris-web-ui.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "iris-web-ui.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
