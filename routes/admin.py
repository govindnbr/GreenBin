from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, session
from flask_login import login_required, current_user
from models.models import db, QRCode, User, PlasticDrop, TrashBin, Redemption
from datetime import datetime, timedelta
import uuid
import qrcode
import io
import base64
from PIL import Image

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check admin credentials
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Admin logged out successfully!', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with QR code management"""
    # Get QR code statistics
    total_qr_codes = QRCode.query.count()
    used_qr_codes = QRCode.query.filter_by(is_used=True).count()
    pending_qr_codes = total_qr_codes - used_qr_codes
    
    # Get recent QR codes with user information
    recent_qr_codes = db.session.query(QRCode, User)\
                               .outerjoin(User, QRCode.used_by == User.id)\
                               .order_by(QRCode.created_at.desc())\
                               .limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_qr_codes=total_qr_codes,
                         used_qr_codes=used_qr_codes,
                         pending_qr_codes=pending_qr_codes,
                         recent_qr_codes=recent_qr_codes)

@admin_bp.route('/generate_qr', methods=['POST'])
@admin_required
def generate_qr():
    """Generate QR code with specified points"""
    try:
        points = int(request.json.get('points', 10))
        
        # Generate unique QR code
        qr_code = str(uuid.uuid4())[:12].upper()
        
        # Create QR code record
        new_qr = QRCode(
            code=qr_code,
            trash_bin_id=1,  # Default trash bin
            plastic_type='admin_generated',
            points_value=points,
            is_used=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_qr)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'QR code generated successfully!',
            'qr_code': qr_code,
            'points': points
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating QR code: {str(e)}'
        })

@admin_bp.route('/qr_image/<qr_code>')  
@admin_required
def qr_image(qr_code):
    """Generate and serve QR code image"""
    try:
        # Create QR code instance with better settings for phone scanning
        qr = qrcode.QRCode(
            version=None,  # Auto-size
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
            box_size=10,  # Size of each box
            border=4,  # Border size
        )
        qr.add_data(qr_code)
        qr.make(fit=True)

        # Create image with white background and black foreground
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Ensure image is large enough for phone scanning (minimum 200x200)
        if img.size[0] < 200:
            new_size = (200, 200)
            img = img.resize(new_size, Image.NEAREST)
        
        # Save to BytesIO
        img_io = io.BytesIO()
        img.save(img_io, 'PNG', optimize=False)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        print(f"QR Code generation error: {str(e)}")
        # Return a simple error image or 404
        return f"QR Code generation error: {str(e)}", 404

@admin_bp.route('/check_qr_status/<qr_code>')
@admin_required
def check_qr_status(qr_code):
    """Check if QR code has been used"""
    try:
        qr = db.session.query(QRCode, User)\
                       .outerjoin(User, QRCode.used_by == User.id)\
                       .filter(QRCode.code == qr_code)\
                       .first()
        
        if qr:
            qr_obj, user = qr
            return jsonify({
                'is_used': qr_obj.is_used,
                'scanned_by': user.username if user else 'Unknown User',
                'points': qr_obj.points_value,
                'scanned_at': qr_obj.used_at.isoformat() if qr_obj.used_at else None
            })
        else:
            return jsonify({'error': 'QR code not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/qr_history')
@admin_required
def qr_history():
    """View QR code history and status"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    qr_codes = QRCode.query.order_by(QRCode.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/qr_history.html', qr_codes=qr_codes)

@admin_bp.route('/users')
@admin_required
def users_management():
    """View and manage all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search))
        )
    
    users = query.order_by(User.created_at.desc())\
               .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/user/<int:user_id>')
@admin_required
def user_details(user_id):
    """View detailed user information and transactions"""
    user = User.query.get_or_404(user_id)
    
    # Get user's plastic drops (points earned)
    plastic_drops = PlasticDrop.query.filter_by(user_id=user_id)\
                                   .order_by(PlasticDrop.created_at.desc())\
                                   .limit(50).all()
    
    # Get user's redemptions
    redemptions = Redemption.query.filter_by(user_id=user_id)\
                                 .order_by(Redemption.created_at.desc())\
                                 .limit(50).all()
    
    # Get user statistics
    total_drops = PlasticDrop.query.filter_by(user_id=user_id).count()
    total_redemptions = Redemption.query.filter_by(user_id=user_id).count()
    total_points_earned = sum([drop.points_earned for drop in plastic_drops])
    total_points_redeemed = sum([redemption.points_used for redemption in redemptions])
    
    return render_template('admin/user_details.html',
                         user=user,
                         plastic_drops=plastic_drops,
                         redemptions=redemptions,
                         stats={
                             'total_drops': total_drops,
                             'total_redemptions': total_redemptions,
                             'total_points_earned': total_points_earned,
                             'total_points_redeemed': total_points_redeemed
                         })

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user information"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update user information
            if 'email' in data:
                user.email = data['email']
            
            if 'username' in data:
                # Check if username already exists
                existing_user = User.query.filter(User.username == data['username'], User.id != user_id).first()
                if existing_user:
                    return jsonify({'success': False, 'message': 'Username already exists'})
                user.username = data['username']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    return jsonify({'success': False, 'message': 'Invalid request method'})

@admin_bp.route('/user/<int:user_id>/points', methods=['POST'])
@admin_required
def manage_user_points(user_id):
    """Add or subtract points from user account"""
    user = User.query.get_or_404(user_id)
    
    try:
        data = request.get_json()
        points_change = int(data.get('points', 0))
        action = data.get('action', 'add')  # 'add' or 'subtract'
        reason = data.get('reason', 'Admin adjustment')
        
        if action == 'subtract':
            points_change = -abs(points_change)
        else:
            points_change = abs(points_change)
        
        # Check if user has enough points for subtraction
        if points_change < 0 and user.total_points < abs(points_change):
            return jsonify({
                'success': False,
                'message': 'User does not have enough points'
            })
        
        # Update user points
        user.total_points += points_change
        
        # Create a record of this admin action (using PlasticDrop for tracking)
        admin_drop = PlasticDrop(
            user_id=user_id,
            trash_bin_id=1,  # Default bin
            qr_code=f"ADMIN_ADJUST_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            plastic_type='admin_adjustment',
            points_earned=points_change,
            created_at=datetime.utcnow()
        )
        
        db.session.add(admin_drop)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully {"added" if points_change > 0 else "subtracted"} {abs(points_change)} points',
            'new_total': user.total_points
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user account and all associated data"""
    user = User.query.get_or_404(user_id)
    
    try:
        # Delete user's plastic drops
        PlasticDrop.query.filter_by(user_id=user_id).delete()
        
        # Delete user's redemptions
        Redemption.query.filter_by(user_id=user_id).delete()
        
        # Update QR codes used by this user
        QRCode.query.filter_by(used_by=user_id).update({'used_by': None})
        
        # Delete user
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User "{username}" has been deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/delete_qr/<int:qr_id>', methods=['POST'])
@admin_required
def delete_qr(qr_id):
    """Delete a QR code"""
    try:
        qr = QRCode.query.get_or_404(qr_id)
        
        # Check if QR code is already used
        if qr.is_used:
            return jsonify({
                'success': False,
                'message': 'Cannot delete used QR code'
            })
        
        qr_code = qr.code
        db.session.delete(qr)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'QR code "{qr_code}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/setup_demo')
def setup_demo():
    """Create demo data for hackathon presentation"""
    try:
        # Create all database tables
        db.create_all()
        
        # Check if demo user already exists
        existing_user = User.query.filter_by(username='demo').first()
        if existing_user:
            return jsonify({
                'status': 'info',
                'message': 'Demo data already exists! Login with username: demo, password: demo123'
            })
        
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@recycling.com',
            password_hash=generate_password_hash('demo123'),
            total_points=250,
            created_at=datetime.utcnow()
        )
        db.session.add(demo_user)
        db.session.flush()  # Get the user ID
        
        # Create some demo QR codes for testing
        demo_qr_codes = [
            {'code': 'DEMO-QR-001', 'points': 10},
            {'code': 'DEMO-QR-002', 'points': 15},
            {'code': 'DEMO-QR-003', 'points': 5},
            {'code': 'DEMO-QR-004', 'points': 25},
            {'code': 'TEST-CODE-1', 'points': 20},
        ]
        
        # Check if trash bin exists, create if not
        trash_bin = TrashBin.query.first()
        if not trash_bin:
            trash_bin = TrashBin(
                bin_id='BIN001',
                location='Demo Location',
                current_load=0,
                max_capacity=100,
                created_at=datetime.utcnow()
            )
            db.session.add(trash_bin)
            db.session.flush()
        
        # Create demo QR codes
        for qr_data in demo_qr_codes:
            existing_qr = QRCode.query.filter_by(code=qr_data['code']).first()
            if not existing_qr:
                demo_qr = QRCode(
                    code=qr_data['code'],
                    trash_bin_id=trash_bin.id,
                    plastic_type='demo_bottle',
                    points_value=qr_data['points'],
                    is_used=False,
                    created_at=datetime.utcnow()
                )
                db.session.add(demo_qr)
        
        # Create sample plastic drops with realistic data
        drop_data = [
            {'days_ago': 0, 'points': 10, 'qr': 'QR2025001'},
            {'days_ago': 1, 'points': 15, 'qr': 'QR2025002'},
            {'days_ago': 2, 'points': 10, 'qr': 'QR2025003'},
            {'days_ago': 3, 'points': 20, 'qr': 'QR2025004'},
            {'days_ago': 5, 'points': 10, 'qr': 'QR2025005'},
            {'days_ago': 7, 'points': 15, 'qr': 'QR2025006'},
            {'days_ago': 10, 'points': 10, 'qr': 'QR2025007'},
            {'days_ago': 14, 'points': 25, 'qr': 'QR2025008'},
            {'days_ago': 21, 'points': 10, 'qr': 'QR2025009'},
            {'days_ago': 28, 'points': 15, 'qr': 'QR2025010'},
        ]
        
        for drop_info in drop_data:
            drop = PlasticDrop(
                user_id=demo_user.id,
                points_earned=drop_info['points'],
                drop_date=datetime.utcnow() - timedelta(days=drop_info['days_ago']),
                qr_code=drop_info['qr']
            )
            db.session.add(drop)
        
        # Create sample redemption history
        redemption1 = Redemption(
            user_id=demo_user.id,
            points_used=100,
            redemption_type='gift_card',
            status='completed',
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        
        redemption2 = Redemption(
            user_id=demo_user.id,
            points_used=50,
            redemption_type='coupon',
            status='pending',
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        
        db.session.add(redemption1)
        db.session.add(redemption2)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Demo data created successfully!',
            'credentials': {
                'username': 'demo',
                'password': 'demo123'
            },
            'stats': {
                'total_drops': len(drop_data),
                'total_points': sum([drop['points'] for drop in drop_data]),
                'redemptions': 2
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error creating demo data: {str(e)}'
        })

@admin_bp.route('/reset_demo')
def reset_demo():
    """Reset demo data for fresh hackathon presentation"""
    try:
        # Delete all demo user related data
        demo_user = User.query.filter_by(username='demo').first()
        if demo_user:
            PlasticDrop.query.filter_by(user_id=demo_user.id).delete()
            Redemption.query.filter_by(user_id=demo_user.id).delete()
            db.session.delete(demo_user)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Demo data reset successfully!'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error resetting demo data: {str(e)}'
        })

@admin_bp.route('/admin_panel')
def admin_panel():
    """Admin dashboard for hackathon management"""
    user_count = User.query.count()
    total_drops = PlasticDrop.query.count()
    total_redemptions = Redemption.query.count()
    
    return render_template('admin/panel.html', 
                         user_count=user_count,
                         total_drops=total_drops,
                         total_redemptions=total_redemptions)

@admin_bp.route('/bins')
def trash_bins():
    """Trash bin management dashboard"""
    bins = TrashBin.query.all()
    
    # Calculate statistics for each bin
    bin_stats = []
    for bin in bins:
        drops_count = PlasticDrop.query.filter_by(trash_bin_id=bin.id).count()
        bin_stats.append({
            'bin': bin,
            'drops_count': drops_count,
            'status_color': 'danger' if bin.current_load >= 90 else 'warning' if bin.current_load >= 70 else 'success'
        })
    
    return render_template('admin/bins.html', bin_stats=bin_stats)

@admin_bp.route('/bins/<int:bin_id>/empty', methods=['POST'])
def empty_bin(bin_id):
    """Mark a trash bin as emptied"""
    try:
        bin = TrashBin.query.get_or_404(bin_id)
        bin.current_load = 0
        bin.last_emptied = datetime.utcnow()
        bin.status = 'active'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bin {bin.bin_id} has been emptied successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while emptying the bin'
        }), 500

@admin_bp.route('/bins/<int:bin_id>/status', methods=['POST'])
def update_bin_status(bin_id):
    """Update trash bin status"""
    try:
        bin = TrashBin.query.get_or_404(bin_id)
        new_status = request.json.get('status', 'active')
        
        bin.status = new_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bin {bin.bin_id} status updated to {new_status}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating bin status'
        }), 500
