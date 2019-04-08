manifest:git.installed:
  pkg.installed:
    - pkgs:
      - git

manifest:git.latest:
  git.latest:
    - name: {{ pillar.manifest_url }}
    - target: {{ pillar.manifest_path }}
    - branch: {{ pillar.manifest_branch }}
    - rev: {{ pillar.manifest_branch }}
    - https_user: {{ pillar.github_user }}
    - https_pass: {{ pillar.github_pass }}
    - require:
      - manifest:git.installed

manifest:file.directory:
  file.directory:
    - name: {{ pillar.manifest_path }}/PRIVATE
    - require:
      - manifest:git.latest

manifest:file.exists:
  file.managed:
    - name: {{ pillar.manifest_path }}/PRIVATE/github_oauth.yml
    - source: salt://github_oauth.yml
    - template: jinja
    - context: {{ pillar }}
    - require:
      - manifest:file.directory