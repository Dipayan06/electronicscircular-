// useAsync — standard loading/error/data pattern (Phase 2 §2.7) so every
// data-fetching page handles the three states consistently. `deps` re-runs the
// fetch; `reload()` re-runs on demand after a mutation.
import { useState, useEffect, useCallback } from 'react';

export default function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const run = useCallback(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    Promise.resolve()
      .then(fn)
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((error) => active && setState({ data: null, loading: false, error: error.message }));
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(run, [run]);

  return { ...state, reload: run };
}
