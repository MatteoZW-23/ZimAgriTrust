"""
JUPYTER NOTEBOOK EXECUTOR
Executes notebooks and extracts results
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotebookExecutor:
    """
    Executes Jupyter notebooks and captures outputs
    """
    
    def __init__(self):
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if papermill is available"""
        try:
            import papermill
            self.use_papermill = True
        except ImportError:
            logger.warning("papermill not installed, using nbconvert")
            self.use_papermill = False
    
    def execute_notebook(self, notebook_path, parameters=None, timeout_seconds=3600):
        """
        Execute a Jupyter notebook
        
        Args:
            notebook_path: Path to .ipynb file
            parameters: Dict of parameters to inject
            timeout_seconds: Max execution time
        
        Returns:
            Dict with execution results
        """
        
        notebook_path = Path(notebook_path)
        
        if not notebook_path.exists():
            return {
                'success': False,
                'error': f"Notebook not found: {notebook_path}"
            }
        
        # Create output path with timestamp
        output_dir = notebook_path.parent / 'executed'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"{notebook_path.stem}_{timestamp}.ipynb"
        
        start_time = datetime.now()
        
        try:
            if self.use_papermill:
                result = self._execute_with_papermill(
                    notebook_path, output_path, parameters
                )
            else:
                result = self._execute_with_nbconvert(
                    notebook_path, output_path, parameters
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'output_path': str(output_path),
                'execution_time': execution_time,
                'notebook_name': notebook_path.stem
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Timeout after {timeout_seconds} seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_with_papermill(self, input_path, output_path, parameters):
        """Execute using papermill (supports parameters)"""
        import papermill as pm
        
        pm.execute_notebook(
            input_path=str(input_path),
            output_path=str(output_path),
            parameters=parameters or {},
            kernel_name='python3',
            progress_bar=False,
            log_output=True
        )
        
        return output_path
    
    def _execute_with_nbconvert(self, input_path, output_path, parameters):
        """Execute using nbconvert (fallback)"""
        
        cmd = [
            sys.executable, '-m', 'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            f'--output={output_path.name}',
            f'--output-dir={output_path.parent}',
            str(input_path)
        ]
        
        # Inject parameters via environment variables
        env = os.environ.copy()
        if parameters:
            env['NOTEBOOK_PARAMETERS'] = json.dumps(parameters)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
            env=env
        )
        
        if result.returncode != 0:
            raise Exception(f"nbconvert failed: {result.stderr}")
        
        return output_path
    
    def extract_results(self, executed_notebook_path):
        """
        Extract results from executed notebook
        Looks for specific output cells marked with # OUTPUT:
        """
        
        import nbformat
        
        with open(executed_notebook_path, 'r') as f:
            notebook = nbformat.read(f, as_version=4)
        
        results = {
            'accuracy': None,
            'metrics': {},
            'predictions': {},
            'model_weights_path': None,
            'insights': []
        }
        
        # Scan cells for outputs
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                
                # Check for output markers
                source = cell.source
                
                if '# OUTPUT: accuracy' in source:
                    # Extract accuracy from outputs
                    if cell.outputs:
                        for output in cell.outputs:
                            if 'text' in output:
                                results['accuracy'] = self._parse_float(output['text'])
                
                elif '# OUTPUT: metrics' in source:
                    if cell.outputs:
                        results['metrics'] = self._parse_json(cell.outputs)
                
                elif '# OUTPUT: predictions' in source:
                    if cell.outputs:
                        results['predictions'] = self._parse_json(cell.outputs)
                
                elif '# OUTPUT: model_path' in source:
                    if cell.outputs:
                        results['model_weights_path'] = self._parse_string(cell.outputs)
                
                elif '# OUTPUT: insight' in source:
                    if cell.outputs:
                        results['insights'].append(self._parse_string(cell.outputs))
        
        return results
    
    def _parse_float(self, text):
        """Extract float from cell output"""
        try:
            return float(text.strip())
        except:
            return None
    
    def _parse_json(self, outputs):
        """Parse JSON from cell output"""
        for output in outputs:
            if 'text' in output:
                try:
                    return json.loads(output['text'])
                except:
                    pass
        return {}
    
    def _parse_string(self, outputs):
        """Extract string from cell output"""
        for output in outputs:
            if 'text' in output:
                return output['text'].strip()
        return None
