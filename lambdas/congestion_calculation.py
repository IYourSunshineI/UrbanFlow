
def calculate_congestion_index(speed_limit, avg_speed):
    """
    Calculate the congestion index based on speed limit and average speed.
    Formula: CI = (vlimit - vavg) / vlimit
    where CI is the congestion index, vlimit is the speed limit, and vavg is the average speed.
    """
    if avg_speed <= 0:
        return 999.0 # stopped traffic

    ci = (speed_limit - avg_speed) / avg_speed
    ci = max(0.0, ci)
    print(f"Calculating congestion index: {ci}")
    return ci

def lambda_handler(event, context):
    """
    AWS Lambda function to calculate congestion index from speed limit and average speed.
    Expects event to contain 'speed_limit' and 'avg_speed' keys.
    """
    try:
        speed_limit = float(event.get('speed_limit', 0))
        avg_speed = float(event.get('avg_speed', 0))

        ci = calculate_congestion_index(speed_limit, avg_speed)

        return {
            'statusCode': 200,
            'congestion_index': ci
        }

    except Exception as e:
        print(f"Error calculating congestion index: {e}")
        return {
            'statusCode': 500,
            'error': str(e)
        }