"""
OpenGL Support Check Script

This script checks for OpenGL support and gathers system information.
"""
import sys
import platform as sys_platform
import logging
from PyQt6.QtCore import QLibraryInfo

def check_opengl_support():
    """Check for OpenGL support and return a dictionary with the results."""
    results = {
        'system': {},
        'python': {},
        'opengl': {},
        'pyqt6': {}
    }
    
    # System information
    results['system'] = {
        'os': sys_platform.system(),
        'os_version': sys_platform.version(),
        'machine': sys_platform.machine(),
        'processor': sys_platform.processor(),
        'python_version': sys_platform.python_version(),
    }
    
    # PyQt6 information
    try:
        from PyQt6.QtOpenGL import QOpenGLVersionProfile, QOpenGLContext, QOpenGLFunctions
        from PyQt6.QtGui import QSurfaceFormat, QOpenGLContext
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
        
        results['pyqt6']['opengl_available'] = True
        
        # Check OpenGL version
        format = QSurfaceFormat()
        results['opengl']['version'] = {
            'major': format.majorVersion(),
            'minor': format.minorVersion(),
            'profile': format.profile().name if hasattr(format, 'profile') else 'Unknown',
            'renderer': 'Unknown',
            'vendor': 'Unknown',
            'shading_language': 'Unknown'
        }
        
        # Try to get more detailed OpenGL info
        try:
            from OpenGL import GL, platform
            import ctypes
            
            # Create a hidden window to get OpenGL context
            from PyQt6.QtWidgets import QApplication, QOpenGLWidget
            import sys
            
            app = QApplication.instance() or QApplication(sys.argv)
            
            class GLWidget(QOpenGLWidget):
                def initializeGL(self):
                    self.gl = self.context().versionFunctions()
                    if self.gl:
                        self.gl.initializeOpenGLFunctions()
                        results['opengl']['version']['renderer'] = self.gl.glGetString(GL.GL_RENDERER).decode('utf-8')
                        results['opengl']['version']['vendor'] = self.gl.glGetString(GL.GL_VENDOR).decode('utf-8')
                        results['opengl']['version']['shading_language'] = self.gl.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode('utf-8')
            
            widget = GLWidget()
            widget.show()
            app.processEvents()
            widget.close()
            
        except Exception as e:
            results['opengl']['error'] = str(e)
            
    except ImportError as e:
        results['pyqt6']['opengl_available'] = False
        results['pyqt6']['import_error'] = str(e)
    
    return results

def print_results(results):
    """Print the results in a readable format."""
    print("=" * 80)
    print("OpenGL Support Check")
    print("=" * 80)
    
    print("\nSystem Information:")
    print(f"  OS: {results['system']['os']} {results['system']['os_version']}")
    print(f"  Architecture: {results['system']['machine']}")
    print(f"  Processor: {results['system']['processor']}")
    print(f"  Python: {results['system']['python_version']}")
    
    print("\nPyQt6 OpenGL Support:")
    if results['pyqt6'].get('opengl_available', False):
        print("  OpenGL is available")
        print("\nOpenGL Information:")
        print(f"  Version: {results['opengl']['version']['major']}.{results['opengl']['version']['minor']}")
        print(f"  Profile: {results['opengl']['version']['profile']}")
        print(f"  Renderer: {results['opengl']['version'].get('renderer', 'Unknown')}")
        print(f"  Vendor: {results['opengl']['version'].get('vendor', 'Unknown')}")
        print(f"  Shading Language: {results['opengl']['version'].get('shading_language', 'Unknown')}")
    else:
        print("  OpenGL is NOT available")
        print(f"  Error: {results['pyqt6'].get('import_error', 'Unknown error')}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    results = check_opengl_support()
    print_results(results)
