# freelancer_models.py

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='freelancer')
    education  = db.Column(db.String(200))
    experience = db.Column(db.String(200))
    linkedin   = db.Column(db.String(255))

    clients = db.relationship(
        'Client',
        back_populates='freelancer',
        cascade='all, delete-orphan',
        lazy=True
    )


class Client(db.Model):
    __tablename__ = 'clients'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120))
    phone         = db.Column(db.String(20))
    notes         = db.Column(db.Text)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_link = db.Column(db.String(255), nullable=False, default='')


    freelancer = db.relationship(
        'User',
        back_populates='clients'
    )
    projects = db.relationship(
        'Project',
        back_populates='client',
        cascade='all, delete-orphan',
        lazy=True
    )


class Project(db.Model):
    __tablename__ = 'projects'

    id          = db.Column(db.Integer, primary_key=True)
    client_id   = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date  = db.Column(db.Date)
    end_date    = db.Column(db.Date)
    currency    = db.Column(db.String(10))
    status      = db.Column(db.String(20), default='pending')

    client = db.relationship(
        'Client',
        back_populates='projects'
    )

    pricing = db.relationship(
        'PricingProposal',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy=True
    )

    # one-to-one shared link
    shared_link = db.relationship(
        'SharedLink',
        uselist=False,
        back_populates='project',
        cascade='all, delete-orphan'
    )
    meetings     = db.relationship(
                      'Meeting',
                      back_populates='project',
                      cascade='all, delete-orphan',
                      lazy=True
                   )
    revisions = db.relationship(
        'Revision',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy=True
    )
class SharedLink(db.Model):
    __tablename__ = 'shared_links'

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, unique=True)
    token      = db.Column(db.String(64), unique=True, nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship(
        'Project',
        back_populates='shared_link'
    )


class PricingProposal(db.Model):
    __tablename__ = 'pricing_proposals'

    id                = db.Column(db.Integer, primary_key=True)
    project_id        = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    type              = db.Column(db.String(10), nullable=False)   # 'fixed' or 'hourly'
    total_charge      = db.Column(db.Numeric(10,2))                # fixed
    advanced_payment  = db.Column(db.Numeric(10,2), default=0)
    hourly_rate       = db.Column(db.Numeric(10,2))                # hourly
    estimated_hours   = db.Column(db.Integer)                      # hourly
    approved_by_client = db.Column(db.Boolean, default=False)

    project = db.relationship(
        'Project',
        back_populates='pricing'
    )

    stages = db.relationship(
        'PricingStage',
        back_populates='proposal',
        cascade='all, delete-orphan',
        lazy=True
    )

    invoices = db.relationship(
        'Invoice',
        back_populates='proposal',
        cascade='all, delete-orphan',
        lazy=True
    )

    change_requests = db.relationship(
        'ProposalChangeRequest',
        back_populates='proposal',
        cascade='all, delete-orphan',
        lazy=True
    )


class PricingStage(db.Model):
    __tablename__ = 'pricing_stages'

    id            = db.Column(db.Integer, primary_key=True)
    proposal_id   = db.Column(db.Integer, db.ForeignKey('pricing_proposals.id'), nullable=False)
    stage_number  = db.Column(db.Integer, nullable=False)
    tech_details  = db.Column(db.String(200))
    deliverables  = db.Column(db.Text)
    amount        = db.Column(db.Numeric(10,2))    # fixed
    hours         = db.Column(db.Integer)          # hourly
    due_date      = db.Column(db.Date)
    work_status   = db.Column(db.String(20), default='pending')
    payment_status= db.Column(db.String(20), default='pending')

    proposal = db.relationship(
        'PricingProposal',
        back_populates='stages'
    )
    tasks = db.relationship(
        'Task',               
        back_populates='pricing_stage',
        cascade='all, delete-orphan',
        order_by='Task.id'
    )

    statuses = db.relationship(
        'PhaseStatus',
        backref='stage',
        cascade='all, delete-orphan',
        lazy=True
    )
    comments = db.relationship(
        'PhaseComment',
        backref='stage',
        cascade='all, delete-orphan',
        lazy=True
    )




class PhaseStatus(db.Model):
    __tablename__ = 'phase_statuses'

    id       = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('pricing_stages.id'), nullable=False)
    phase    = db.Column(db.String, nullable=False)     # e.g. 'Planning'
    status   = db.Column(db.String, default='Pending')  # Pending / Complete


class PhaseComment(db.Model):
    __tablename__ = 'phase_comments'

    id         = db.Column(db.Integer, primary_key=True)
    stage_id   = db.Column(db.Integer, db.ForeignKey('pricing_stages.id'), nullable=False)
    phase      = db.Column(db.String, nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Invoice(db.Model):
    __tablename__ = 'invoice'

    id           = db.Column(db.Integer, primary_key=True)
    proposal_id  = db.Column(db.Integer, db.ForeignKey('pricing_proposals.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    advance_paid = db.Column(db.Numeric(10,2))
    total_cost   = db.Column(db.Numeric(10,2))
    amount_due   = db.Column(db.Numeric(10,2))

    proposal = db.relationship(
        'PricingProposal',
        back_populates='invoices'
    )
    items = db.relationship(
        'InvoiceItem',
        back_populates='invoice',
        cascade='all, delete-orphan',
        lazy=True
    )


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_item'

    id         = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    stage_no   = db.Column(db.Integer)
    name       = db.Column(db.String(128))
    cost       = db.Column(db.Numeric(10,2))

    invoice = db.relationship(
        'Invoice',
        back_populates='items'
    )


class ProposalChangeRequest(db.Model):
    __tablename__ = 'change_requests'

    id          = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('pricing_proposals.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    proposal = db.relationship(
        'PricingProposal',
        back_populates='change_requests'
    )
class Meeting(db.Model):
    __tablename__ = 'meetings'

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    when       = db.Column(db.DateTime, nullable=False)
    agenda     = db.Column(db.String(255), nullable=False)

    # back‐ref for revisions
    revisions  = db.relationship(
        'Revision',
        back_populates='meeting',
        cascade='all, delete-orphan',
        lazy=True
    )
    project      = db.relationship(
                      'Project',
                      back_populates='meetings'
                   )

class Revision(db.Model):
    __tablename__ = 'revisions'
    id         = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    notes      = db.Column(db.Text, nullable=False)
    cost       = db.Column(db.Numeric(10,2), default=0)                   # ← new
    is_paid    = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('projects.id'),
        nullable=False,                     # <— make this NOT NULL
    )

    

    meeting    = db.relationship('Meeting', back_populates='revisions')
    project    = db.relationship('Project', back_populates='revisions')

from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    text       = db.Column(db.Text,  nullable=False)
    is_read    = db.Column(db.Boolean, default=False, nullable=False)     # ← new
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project    = db.relationship('Project', back_populates='notifications')

Project.notifications = db.relationship(
    'Notification',
    back_populates='project',
    cascade='all,delete-orphan',
    lazy=True
)

# on your Project model, append:
Project.notifications = db.relationship(
    'Notification',
    back_populates='project',
    cascade='all, delete-orphan',
    lazy=True
)
class Task(db.Model):
    __tablename__ = 'tasks'  
    # ❌ This must match exactly the table name you see in SSMS (`dbo.tasks`).

    id           = db.Column(db.Integer, primary_key=True)
    stage_id     = db.Column(
                      db.Integer, 
                      db.ForeignKey('pricing_stages.id'),  # ← EXACTLY the plural table name
                      nullable=False
                  )
    description  = db.Column(db.Text, nullable=False)
    start_date   = db.Column(db.Date, nullable=True)
    end_date     = db.Column(db.Date, nullable=True)
    remarks      = db.Column(db.String(255), nullable=True)
    is_done      = db.Column(db.Boolean, default=False)

    # ─── This relationship must exactly match PricingStage.tasks’ back_populates: ───
    pricing_stage = db.relationship(
        'PricingStage',
        back_populates='tasks'
    )


# Example of how PricingProposal back_populates into PricingStage.stages
PricingProposal.stages = db.relationship(
    'PricingStage',
    back_populates='proposal',
    cascade='all, delete-orphan'
)