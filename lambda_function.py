import boto3
import json
import uuid
import os
from botocore.config import Config

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('RESULTS_TABLE', 'deep_research_results')

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        response = _response(200, {})
        print(f"OPTIONS response: {json.dumps(response)}")
        return response
    
    # Background async execution (invoked by self)
    if event.get('_async'):
        print(f"Processing async request for session: {event['session_id']}")
        _do_agent_work(event['session_id'], event['prompt'])
        async_response = {'statusCode': 200}
        print(f"Async processing response: {json.dumps(async_response)}")
        return async_response

    # Poll: GET /deep_research?session_id=xxx
    if event.get('httpMethod') == 'GET':
        try:
            query_params = event.get('queryStringParameters') or {}
            session_id = query_params.get('session_id')
            
            print(f"GET request for session_id: {session_id}")
            
            if not session_id:
                response = _response(400, {'error': 'session_id parameter required'})
                print(f"GET error response (missing session_id): {json.dumps(response)}")
                return response
            
            table = dynamodb.Table(TABLE_NAME)
            item = table.get_item(Key={'session_id': session_id}).get('Item')
            
            print(f"DynamoDB item for session {session_id}: {json.dumps(item, default=str) if item else 'None'}")
            
            if not item:
                response = _response(404, {'status': 'NOT_FOUND', 'message': 'Session not found'})
                print(f"GET response (session not found): {json.dumps(response)}")
                return response
            
            status = item.get('status', 'PENDING')
            print(f"Current status for session {session_id}: {status}")
            
            if status == 'DONE':
                response_body = {
                    'result': item['result'], 
                    'status': 'DONE',
                    'message': 'Research completed successfully'
                }
                response = _response(200, response_body)
                print(f"GET response (DONE) for session {session_id}: Status={response['statusCode']}, Body size={len(response['body'])} chars")
                # Log first 500 chars of result for debugging (avoid huge logs)
                result_preview = str(item['result'])[:500] + "..." if len(str(item['result'])) > 500 else str(item['result'])
                print(f"Result preview: {result_preview}")
                return response
                
            elif status == 'ERROR':
                response_body = {
                    'status': 'ERROR',
                    'message': item.get('error', 'Processing failed'),
                    'error': item.get('error', 'Unknown error')
                }
                response = _response(200, response_body)
                print(f"GET response (ERROR) for session {session_id}: {json.dumps(response)}")
                return response
                
            elif status == 'PROCESSING':
                response_body = {
                    'status': 'PROCESSING',
                    'message': 'Research in progress...'
                }
                response = _response(200, response_body)
                print(f"GET response (PROCESSING) for session {session_id}: {json.dumps(response)}")
                return response
                
            else:  # PENDING
                response_body = {
                    'status': 'PENDING',
                    'message': 'Research request queued'
                }
                response = _response(200, response_body)
                print(f"GET response (PENDING) for session {session_id}: {json.dumps(response)}")
                return response
                
        except Exception as e:
            print(f"Error in GET handler: {str(e)}")
            response = _response(500, {'error': f'Error checking status: {str(e)}'})
            print(f"GET error response (exception): {json.dumps(response)}")
            return response

    # POST: start research
    try:
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        print(f"POST request body: {json.dumps(body)}")
        
        user_input = body.get('prompt')
        print(f"User Input: {user_input}")
        if not user_input:
            response = _response(400, {'error': 'prompt is required'})
            print(f"POST error response (missing prompt): {json.dumps(response)}")
            return response
        
        session_id = f"deep_research_{str(uuid.uuid4()).replace('-', '')}"
        
        print(f"Starting research for session: {session_id} with prompt: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")
        
        # Store pending status
        dynamodb.Table(TABLE_NAME).put_item(Item={
            'session_id': session_id,
            'status': 'PENDING'
        })
        print(f"Stored PENDING status in DynamoDB for session: {session_id}")

        # Invoke self asynchronously with the actual work
        async_payload = {
            '_async': True, 
            'session_id': session_id, 
            'prompt': user_input
        }
        
        lambda_client.invoke(
            FunctionName=context.function_name,
            InvocationType='Event',  # async
            Payload=json.dumps(async_payload)
        )
        print(f"Invoked async Lambda for session: {session_id}")

        response_body = {
            'session_id': session_id, 
            'status': 'PENDING',
            'message': 'Research started. Use session_id to check status.'
        }
        response = _response(202, response_body)
        print(f"POST response (success): {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"Error in POST handler: {str(e)}")
        response = _response(500, {'error': f'Error starting research: {str(e)}'})
        print(f"POST error response (exception): {json.dumps(response)}")
        return response


def _do_agent_work(session_id, user_input):
    """Process the Bedrock agent request in background"""
    try:
        print(f"Starting Bedrock agent work for session: {session_id}")
        print(f"User input for session {session_id}: '{user_input[:200]}{'...' if len(user_input) > 200 else ''}'")
        
        # Update status to processing
        dynamodb.Table(TABLE_NAME).put_item(Item={
            'session_id': session_id,
            'status': 'PROCESSING'
        })
        print(f"Updated status to PROCESSING for session: {session_id}")
        
        # Configure Bedrock client with timeout
        config = Config(
            read_timeout=600,  # 10 minutes
            connect_timeout=60,  # 1 minute
            retries={'max_attempts': 3}
        )
        
        client = boto3.client('bedrock-agentcore', region_name='us-east-1', config=config)
        payload = json.dumps({"topic": user_input})
        
        print(f"Invoking Bedrock agent for session: {session_id}")
        print(f"Bedrock payload: {payload[:300]}{'...' if len(payload) > 300 else ''}")
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn='AGENT_RUNTIME_ARN', # Starts with -> arn:aws:bedrock-agentcore
            runtimeSessionId=session_id,
            payload=payload,
        )
        
        response_body = response['response'].read()
        result = json.loads(response_body)
        
        print(f"Bedrock agent completed for session: {session_id}")
        print(f"Bedrock response size: {len(response_body)} bytes")
        print(f"Bedrock result preview: {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}")
        
        # Store successful result
        dynamodb.Table(TABLE_NAME).put_item(Item={
            'session_id': session_id,
            'status': 'DONE',
            'result': result
        })
        print(f"Stored DONE status and result in DynamoDB for session: {session_id}")
        
    except Exception as e:
        print(f"Error in agent work for session {session_id}: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        
        # Store error status
        dynamodb.Table(TABLE_NAME).put_item(Item={
            'session_id': session_id,
            'status': 'ERROR',
            'error': str(e)
        })
        print(f"Stored ERROR status in DynamoDB for session: {session_id}")


def _response(status_code, body):
    """Generate HTTP response with CORS headers"""
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body)
    }
    
    # Log response details (but not the full body for large responses)
    body_size = len(response['body'])
    print(f"Generated response: StatusCode={status_code}, BodySize={body_size} chars, Headers={response['headers']}")
    
    # For debugging, log the actual body for small responses
    if body_size < 1000:
        print(f"Response body: {response['body']}")
    else:
        print(f"Response body (truncated): {response['body'][:500]}...")
    
    return response
