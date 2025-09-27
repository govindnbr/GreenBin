from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.models import db, QRCode, PlasticDrop, TrashBin, User
from datetime import datetime, timedelta
import random

api_bp = Blueprint('api', __name__)

@api_bp.route('/scan_qr', methods=['POST'])
@login_required
def scan_qr():
    """Simulate QR code scanning and point earning"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
            
        qr_code = data.get('qr_code', '') if data else ''
        
        if not qr_code:
            return jsonify({'success': False, 'message': 'QR code is required'}), 400
        
        # Find the QR code in database
        qr = QRCode.query.filter_by(code=qr_code, is_used=False).first()
        
        if not qr:
            return jsonify({'success': False, 'message': 'Invalid or already used QR code'}), 400
        
        # Mark QR code as used
        qr.is_used = True
        qr.used_at = datetime.utcnow()
        qr.used_by = current_user.id
        
        # Create plastic drop record
        plastic_drop = PlasticDrop(
            user_id=current_user.id,
            trash_bin_id=qr.trash_bin_id,
            qr_code=qr_code,
            plastic_type=qr.plastic_type,
            points_earned=qr.points_value
        )
        
        # Update user points
        current_user.total_points += qr.points_value
        
        # Update trash bin load (simulate)
        trash_bin = TrashBin.query.get(qr.trash_bin_id)
        if trash_bin:
            trash_bin.current_load = min(100, trash_bin.current_load + random.randint(1, 5))
        
        db.session.add(plastic_drop)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'points_earned': qr.points_value,
            'total_points': current_user.total_points,
            'message': f'Successfully earned {qr.points_value} points!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@api_bp.route('/generate_qr', methods=['POST'])
def generate_qr():
    """Generate a new QR code (for trash bin simulation)"""
    try:
        data = request.get_json()
        bin_id = data.get('bin_id', 'BIN001')
        
        trash_bin = TrashBin.query.filter_by(bin_id=bin_id).first()
        if not trash_bin:
            return jsonify({'success': False, 'message': 'Trash bin not found'}), 404
        
        # Generate new QR code
        from models.models import generate_qr_code
        new_qr = QRCode(
            code=generate_qr_code(),
            trash_bin_id=trash_bin.id,
            plastic_type='bottle',
            points_value=10
        )
        
        db.session.add(new_qr)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'qr_code': new_qr.code,
            'bin_location': trash_bin.location,
            'points_value': new_qr.points_value
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@api_bp.route('/user_stats')
@login_required
def user_stats():
    """Get user statistics for dashboard"""
    try:
        # Get user's plastic drops
        drops = PlasticDrop.query.filter_by(user_id=current_user.id).all()
        
        # Calculate statistics
        total_drops = len(drops)
        total_points = current_user.total_points
        
        # Daily stats (last 7 days)
        daily_stats = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            day_drops = [d for d in drops if d.created_at.date() == date.date()]
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'drops': len(day_drops),
                'points': sum(d.points_earned for d in day_drops)
            })
        
        # Monthly stats (last 12 months)
        monthly_stats = []
        for i in range(12):
            date = datetime.utcnow() - timedelta(days=i*30)
            month_drops = [d for d in drops if d.created_at.month == date.month and d.created_at.year == date.year]
            monthly_stats.append({
                'month': date.strftime('%Y-%m'),
                'drops': len(month_drops),
                'points': sum(d.points_earned for d in month_drops)
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_drops': total_drops,
                'total_points': total_points,
                'daily_stats': daily_stats[::-1],  # Reverse to show oldest first
                'monthly_stats': monthly_stats[::-1]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@api_bp.route('/redeem', methods=['POST'])
@login_required
def redeem_points():
    """Redeem points for rewards"""
    try:
        data = request.get_json()
        redemption_type = data.get('type')  # coupon, gift_card, bank_transfer
        points_to_redeem = int(data.get('points', 0))
        
        if points_to_redeem <= 0:
            return jsonify({'success': False, 'message': 'Invalid points amount'}), 400
        
        if current_user.total_points < points_to_redeem:
            return jsonify({'success': False, 'message': 'Insufficient points'}), 400
        
        # Calculate value (1 point = $0.01)
        value = points_to_redeem * 0.01
        
        # Create redemption record
        from models.models import Redemption
        redemption = Redemption(
            user_id=current_user.id,
            redemption_type=redemption_type,
            points_used=points_to_redeem,
            value=value,
            status='completed'
        )
        
        # Generate coupon code if needed
        if redemption_type in ['coupon', 'gift_card']:
            redemption.coupon_code = f"{redemption_type.upper()}{random.randint(100000, 999999)}"
        
        # Update user points
        current_user.total_points -= points_to_redeem
        
        db.session.add(redemption)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully redeemed {points_to_redeem} points',
            'redemption': {
                'type': redemption_type,
                'value': value,
                'coupon_code': redemption.coupon_code,
                'remaining_points': current_user.total_points
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

