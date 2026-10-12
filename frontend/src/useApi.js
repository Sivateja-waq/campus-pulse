import { useEffect, useState } from "react";

// tiny fetch hook: re-runs whenever deps change
export function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true }));
    fn()
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
