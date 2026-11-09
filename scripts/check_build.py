"""Build sdist and wheel, then smoke-test the wheel away from the source checkout."""
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
with tempfile.TemporaryDirectory(prefix='indian-quant-build-') as temporary:
    temporary = Path(temporary)
    dist = temporary / 'dist'
    subprocess.run([sys.executable, '-m', 'build', '--no-isolation', '--outdir', str(dist), str(root)], check=True)
    wheel, = dist.glob('*.whl')
    source, = dist.glob('*.tar.gz')
    assert source.stat().st_size > 0
    with zipfile.ZipFile(wheel) as archive:
        assert 'indian_quant/evidence.py' in archive.namelist()
        metadata = archive.read(f'indian_quant-{version}.dist-info/METADATA').decode()
        assert f'Version: {version}' in metadata
        assert 'git+https://github.com/maheshwaripn/Indian_Trader_skill.git@' in metadata
    target = temporary / 'installed'
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--target', str(target), str(wheel)], check=True)
    env = {**os.environ, 'PYTHONPATH': str(target)}
    result = subprocess.check_output([sys.executable, '-m', 'indian_quant', 'doctor'], cwd=temporary, env=env, text=True)
    assert json.loads(result)['live_execution'] is False
    check = 'import indian_quant; print(indian_quant.__version__); print(indian_quant.__file__)'
    result = subprocess.check_output([sys.executable, '-c', check], cwd=temporary, env=env, text=True)
    assert version == result.splitlines()[0]
    assert str(target) in result.splitlines()[1]
print(f'Built and smoke-tested source/wheel distribution {version}')
