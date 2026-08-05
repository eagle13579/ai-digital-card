import sys, os
sys.path.insert(0, os.getcwd())
print('Testing import chain...')
import app.ai.feedback_loop
print('1. feedback_loop OK')
import app.ai.online_learning
print('2. online_learning OK')

# Now try the heavier import
print('3. Trying RecommendEngine import...')
import importlib
spec = importlib.util.find_spec('app.ai.recommendation')
print(f'   Found spec: {spec}')
if spec:
    print(f'   Origin: {spec.origin}')
