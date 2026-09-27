import { useState } from 'react';
import Navbar from '../components/Navbar';

interface SettingField {
  key:         string;
  label:       string;
  placeholder: string;
  type:        'text' | 'password' | 'url';
  group:       string;
}

const FIELDS: SettingField[] = [
  // API
  { key: 'VITE_API_URL',             label: 'API Base URL',              placeholder: 'http://localhost:8000/api', type: 'url',      group: 'Application' },
  // GitHub
  { key: 'github_token',             label: 'GitHub Token',              placeholder: 'ghp_…',                   type: 'password', group: 'GitHub' },
  { key: 'github_webhook_secret',    label: 'Webhook Secret',            placeholder: 'your-webhook-secret',     type: 'password', group: 'GitHub' },
  // watsonx
  { key: 'watsonx_api_key',          label: 'watsonx API Key',           placeholder: 'IBMid API key',            type: 'password', group: 'IBM watsonx.ai' },
  { key: 'watsonx_project_id',       label: 'Project ID',                placeholder: 'xxxxxxxx-…',              type: 'text',     group: 'IBM watsonx.ai' },
  { key: 'watsonx_url',              label: 'watsonx URL',               placeholder: 'https://us-south.ml.cloud.ibm.com', type: 'url', group: 'IBM watsonx.ai' },
  // Jira
  { key: 'jira_url',                 label: 'Jira Base URL',             placeholder: 'https://yourorg.atlassian.net', type: 'url', group: 'Jira' },
  { key: 'jira_email',              label: 'Jira Email',                 placeholder: 'you@example.com',         type: 'text',     group: 'Jira' },
  { key: 'jira_api_token',           label: 'Jira API Token',            placeholder: 'Jira personal access token', type: 'password', group: 'Jira' },
];

const GROUPS = [...new Set(FIELDS.map((f) => f.group))];

export default function Settings() {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const stored: Record<string, string> = {};
    FIELDS.forEach((f) => {
      stored[f.key] = localStorage.getItem(`devflow_setting_${f.key}`) ?? '';
    });
    return stored;
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    FIELDS.forEach((f) => {
      if (values[f.key]) {
        localStorage.setItem(`devflow_setting_${f.key}`, values[f.key]);
      } else {
        localStorage.removeItem(`devflow_setting_${f.key}`);
      }
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="min-h-screen bg-[#F4F4F4]">
      <Navbar />
      <div className="pt-12">
        <div className="bg-white border-b border-[#D0D0D0] px-6 py-6">
          <div className="max-w-3xl mx-auto">
            <p className="text-label mb-1">Configuration</p>
            <h1 className="text-xl font-semibold text-[#161616]">Settings</h1>
            <p className="text-xs text-[#525252] mt-1">
              Stored in browser localStorage only. For production, configure via server-side <span className="font-mono">.env</span>.
            </p>
          </div>
        </div>

        <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
          {GROUPS.map((group) => (
            <div key={group} className="bg-white border border-[#D0D0D0] p-6">
              <p className="text-sm font-semibold text-[#161616] mb-4">{group}</p>
              <div className="space-y-4">
                {FIELDS.filter((f) => f.group === group).map((field) => (
                  <div key={field.key}>
                    <label className="text-[10px] font-mono text-[#525252] uppercase tracking-wide block mb-1">
                      {field.label}
                    </label>
                    <input
                      type={field.type}
                      value={values[field.key] ?? ''}
                      onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      className="w-full border border-[#D0D0D0] px-3 py-1.5 text-xs font-mono focus:outline-none focus:border-[#0F62FE]"
                      autoComplete="off"
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="flex items-center justify-between">
            <p className="text-xs text-[#525252]">
              Settings apply to this browser session. Backend environment variables take precedence.
            </p>
            <button
              onClick={handleSave}
              className="px-5 py-2 bg-[#0F62FE] text-white text-xs font-medium hover:bg-[#0353E9] transition-colors"
            >
              {saved ? '✓ Saved' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
