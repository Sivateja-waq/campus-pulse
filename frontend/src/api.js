async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
  return body;
}

export const api = {
  meta: () => request("/meta/"),
  overview: () => request("/overview/"),
  students: (params) => request(`/students/?${new URLSearchParams(params)}`),
  student: (roll) => request(`/students/${roll}/`),
  segments: () => request("/segments/"),
  dataReport: () => request("/data/"),
  rerun: () => request("/data/rerun/", { method: "POST" }),
  upload: (source, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/data/upload/${source}/`, { method: "POST", body: form });
  },
};
