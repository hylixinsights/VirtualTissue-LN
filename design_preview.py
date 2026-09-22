"""One-shot Jev artwork preview, explicitly separate from complete LN rounds."""
import copy
import json
from pathlib import Path
from server import Studio


class DesignPreview(Studio):
    def __init__(self, directory, count=10):
        if type(count) is not int or not 1 <= count <= 20:
            raise ValueError('A design preview needs 1–20 individual decisions')
        super().__init__(True, 1, 100, 'jev')
        self.directory = Path(directory)
        # Refuse reuse, including a failed/uncertain attempt; opening a preview
        # again must never create another paid request.
        self.directory.mkdir(parents=True, exist_ok=False)
        self.preview = dict(limit=count, status='ready', selected_ids=[],
                            scope='Partial cell sample for visual inspection, not a complete scientific round.',
                            before=self.sim.snapshot(), after=None)
        self.jev.on_audit = lambda record: self.persist()
        self.persist()

    def state(self):
        return dict(**super().state(), design_preview=copy.deepcopy(self.preview))

    def export(self):
        episode = self.sim.export()
        episode.update(provider=self.status(), provider_label='jev',
                       request_audit=copy.deepcopy(self.jev.audit),
                       design_preview=copy.deepcopy(self.preview))
        return episode

    def persist(self):
        # Atomically replace the local receipt at every audit transition.
        target = self.directory / 'preview.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(dict(state=self.state(), episode=self.export()),
                                       allow_nan=False), encoding='utf-8')
        temporary.replace(target)

    def dispatch(self, path, body):
        if path != '/api/step' or self.preview['status'] != 'ready':
            raise ValueError('This visual preview is limited to one sample; no further decisions or resets are enabled.')
        proposals = self.sim.proposals()
        # Stable representative sample across the three supplied art types;
        # selection does not inspect or optimize the returned actions.
        groups = [[r for r in proposals if r['observation']['cell']['kind'] == kind]
                  for kind in ('B', 'CD4', 'DC')]
        rows = []
        while len(rows) < self.preview['limit'] and any(groups):
            for group in groups:
                if group and len(rows) < self.preview['limit']:
                    rows.append(group.pop(0))
        if len(rows) != self.preview['limit']:
            raise ValueError('Not enough eligible illustrated cells for the requested sample')
        self.preview.update(status='started', selected_ids=[r['id'] for r in rows])
        self.persist()
        try:
            answers = self.jev.choose(rows, 1)
            self.sim.step(answers, rows, 'jev')
            # The existing kernel advances its mandatory clocks by 30 minutes.
            # The other 90 cells receive no choice and no fixture substitute.
            # Label this partial tick and prevent continuation as an experiment.
            self.preview.update(status='complete', after=self.sim.snapshot())
        except Exception:
            self.preview['status'] = 'failed'
            raise
        finally:
            self.persist()
        return self.state()


class SavedPreview:
    """Read-only local viewer. No credentials and no network-capable provider."""
    def __init__(self, path):
        import secrets
        import threading
        self.document = json.loads(Path(path).read_text(encoding='utf-8'))
        if 'design_preview' not in self.document['state']:
            raise ValueError('Not a design preview receipt')
        self.lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)

    def state(self):
        result = copy.deepcopy(self.document['state'])
        result['provider']['enabled'] = False
        result['provider']['configured'] = False
        return result

    def status(self):
        return self.state()['provider']

    def export(self):
        return copy.deepcopy(self.document['episode'])

    def dispatch(self, path, body):
        raise ValueError('Saved visual preview: no new API calls are enabled.')
