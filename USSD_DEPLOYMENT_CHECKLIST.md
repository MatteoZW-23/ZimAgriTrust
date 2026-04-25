# USSD Deployment Checklist

## ✅ Pre-Deployment Checklist

### Code Quality
- [x] All features implemented
- [x] Code reviewed
- [x] No console.log or debug statements
- [x] Error handling comprehensive
- [x] Input validation complete
- [x] Security best practices followed

### Testing
- [x] Unit tests written (50+ scenarios)
- [x] Integration tests passed
- [ ] Load testing completed
- [ ] Security testing done
- [ ] User acceptance testing (UAT)
- [ ] Cross-network testing (if applicable)

### Documentation
- [x] API documentation complete
- [x] User guide created
- [x] Developer documentation ready
- [x] Architecture diagrams created
- [x] Testing guide available
- [x] Quick reference card made

### Database
- [x] Migration scripts ready
- [x] Backup strategy defined
- [ ] Rollback plan documented
- [x] Indexes optimized
- [x] Data validation rules set

### Security
- [x] PIN hashing implemented (bcrypt)
- [x] Session management secure
- [x] Input validation comprehensive
- [x] SQL injection prevention
- [x] Rate limiting configured
- [ ] Security audit completed
- [ ] Penetration testing done

## 🚀 Deployment Steps

### Step 1: Pre-Deployment
```bash
# 1.1 Backup database
pg_dump agri_trust > backup_$(date +%Y%m%d).sql

# 1.2 Tag release
git tag -a v2.0-ussd -m "USSD Platform v2.0"
git push origin v2.0-ussd

# 1.3 Build Docker images
docker-compose build

# 1.4 Run tests
pytest backend/tests/ -v
```

**Checklist**:
- [ ] Database backed up
- [ ] Code tagged in Git
- [ ] Docker images built
- [ ] All tests passing

### Step 2: Database Migration
```bash
# 2.1 Run migration script
cd backend
python scripts/sync_ussd_pins.py

# 2.2 Verify migration
python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
users = db.query(User).filter(User.ussd_pin_hash.is_(None)).count()
print(f'Users without USSD PIN: {users}')
db.close()
"
```

**Checklist**:
- [ ] Migration script executed
- [ ] All users have ussd_pin_hash
- [ ] No errors in logs
- [ ] Database integrity verified

### Step 3: Service Deployment
```bash
# 3.1 Pull latest code
git pull origin main

# 3.2 Update environment variables
cp .env.example .env
# Edit .env with production values

# 3.3 Start services
docker-compose up -d

# 3.4 Check service health
docker-compose ps
curl http://localhost:8080/
curl http://localhost:5000/
```

**Checklist**:
- [ ] Latest code deployed
- [ ] Environment variables set
- [ ] All services running
- [ ] Health checks passing

### Step 4: Telecom Gateway Integration
```bash
# 4.1 Configure webhook URL
# In telecom gateway dashboard:
# Webhook URL: https://your-domain.com/api/v1/ussd/session
# Method: POST
# Content-Type: application/json

# 4.2 Test webhook
curl -X POST https://your-domain.com/api/v1/ussd/session \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "phone_number": "+263771234567",
    "text": ""
  }'
```

**Checklist**:
- [ ] Webhook URL configured
- [ ] SSL certificate valid
- [ ] Test request successful
- [ ] Response format correct

### Step 5: Smoke Testing
```bash
# 5.1 Test main menu
# Dial *123# from test phone

# 5.2 Test sell flow
# Follow: 1 → Maize → 500 → A → 2.50 → Harare

# 5.3 Test buy flow
# Follow: 2 → 1234 → 1 → 100 → 1

# 5.4 Test wallet
# Follow: 5 → 1234

# 5.5 Test PIN change
# Follow: 7 → 1234 → 5678 → 5678
```

**Checklist**:
- [ ] Main menu displays correctly
- [ ] Sell flow completes successfully
- [ ] Buy flow creates offers
- [ ] Wallet shows correct balances
- [ ] PIN change works
- [ ] All responses < 500ms

### Step 6: Monitoring Setup
```bash
# 6.1 Configure Prometheus
# Edit prometheus.yml

# 6.2 Set up Grafana dashboards
# Import USSD dashboard

# 6.3 Configure alerts
# Edit alertmanager.yml

# 6.4 Test alerts
# Trigger test alert
```

**Checklist**:
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards created
- [ ] Alerts configured
- [ ] Test alerts working
- [ ] On-call rotation set

### Step 7: User Communication
```bash
# 7.1 Send SMS to all users
# "AgriTrust USSD is now live! Dial *123# to buy and sell products from any phone."

# 7.2 Update app with USSD info
# Add banner: "Try USSD: Dial *123#"

# 7.3 Train support team
# Conduct training session

# 7.4 Update documentation
# Publish user guides
```

**Checklist**:
- [ ] Users notified via SMS
- [ ] App updated with USSD info
- [ ] Support team trained
- [ ] User guides published
- [ ] FAQ updated

## 📊 Post-Deployment Monitoring

### First Hour
- [ ] Monitor error rates (target: < 1%)
- [ ] Check response times (target: < 500ms)
- [ ] Verify session creation
- [ ] Watch for crashes
- [ ] Monitor Redis memory

### First Day
- [ ] Review all error logs
- [ ] Check user adoption rate
- [ ] Verify transaction completion
- [ ] Monitor database performance
- [ ] Check SMS delivery rates

### First Week
- [ ] Analyze usage patterns
- [ ] Review user feedback
- [ ] Identify bottlenecks
- [ ] Optimize slow queries
- [ ] Update documentation based on issues

## 🔍 Health Checks

### Automated Checks
```bash
# Backend health
curl http://localhost:8080/

# USSD endpoint
curl -X POST http://localhost:8080/api/v1/ussd/session \
  -H "Content-Type: application/json" \
  -d '{"session_id":"health","phone_number":"+263771234567","text":""}'

# Redis
docker-compose exec redis redis-cli ping

# Database
docker-compose exec postgres pg_isready
```

### Manual Checks
- [ ] Dial *123# from real phone
- [ ] Complete a sell transaction
- [ ] Complete a buy transaction
- [ ] Check wallet balances
- [ ] Verify SMS notifications

## 🚨 Rollback Plan

### If Critical Issues Occur
```bash
# 1. Stop new deployments
docker-compose down

# 2. Restore previous version
git checkout v1.0
docker-compose up -d

# 3. Restore database (if needed)
psql agri_trust < backup_YYYYMMDD.sql

# 4. Notify users
# Send SMS: "USSD temporarily unavailable. Use the app."

# 5. Investigate issues
docker-compose logs -f backend

# 6. Fix and redeploy
```

**Rollback Triggers**:
- Error rate > 5%
- Response time > 2 seconds
- Service crashes
- Data corruption
- Security breach

## 📈 Success Metrics

### Day 1 Targets
- [ ] 100+ unique USSD sessions
- [ ] < 1% error rate
- [ ] < 500ms average response time
- [ ] 95%+ uptime
- [ ] 0 critical bugs

### Week 1 Targets
- [ ] 1,000+ unique USSD sessions
- [ ] 50+ transactions via USSD
- [ ] 80%+ session completion rate
- [ ] < 0.5% error rate
- [ ] Positive user feedback

### Month 1 Targets
- [ ] 10,000+ unique USSD sessions
- [ ] 500+ transactions via USSD
- [ ] 60%+ of users tried USSD
- [ ] 90%+ session completion rate
- [ ] NPS score > 50

## 🔧 Troubleshooting

### Common Issues

#### Issue: "Unregistered phone number"
**Solution**: Run migration script
```bash
python backend/scripts/sync_ussd_pins.py
```

#### Issue: "Backend unavailable"
**Solution**: Check backend service
```bash
docker-compose logs backend
docker-compose restart backend
```

#### Issue: "Session expired"
**Solution**: Increase Redis TTL
```python
# In ussd_service.py
await set_json(session_key, session, ttl_seconds=600)  # 10 minutes
```

#### Issue: Slow responses
**Solution**: Optimize database queries
```bash
# Check slow queries
docker-compose exec postgres psql -U postgres -d agri_trust -c "
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"
```

## 📞 Emergency Contacts

### Technical Team
- **Lead Developer**: Mathew Mabira - +263771234567
- **DevOps**: [Name] - [Phone]
- **Database Admin**: [Name] - [Phone]

### Business Team
- **Product Manager**: [Name] - [Phone]
- **Support Lead**: [Name] - [Phone]

### External Partners
- **Telecom Gateway**: [Provider] - [Support Number]
- **SMS Provider**: [Provider] - [Support Number]
- **Hosting Provider**: [Provider] - [Support Number]

## 📝 Sign-Off

### Deployment Approval
- [ ] Technical Lead: _________________ Date: _______
- [ ] Product Manager: ________________ Date: _______
- [ ] QA Lead: _______________________ Date: _______
- [ ] Security Officer: _______________ Date: _______

### Post-Deployment Verification
- [ ] All services running: ____________ Date: _______
- [ ] Smoke tests passed: _____________ Date: _______
- [ ] Monitoring active: ______________ Date: _______
- [ ] Users notified: _________________ Date: _______

---

**Deployment Version**: 2.0  
**Deployment Date**: __________  
**Deployed By**: __________  
**Status**: ⬜ Pending / ⬜ In Progress / ⬜ Complete
