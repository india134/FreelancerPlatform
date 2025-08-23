from flask import Flask, render_template, redirect, url_for, flash, session, request,abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# forms.py already needs email-validator; pip install email_validator
from forms import FreelancerRegistrationForm, LoginForm, ClientForm, ProjectForm
from freelancer_models import db, User, Client, Project
from forms import PricingProposalForm, PricingStageForm,CSRFOnlyForm
from freelancer_models import PricingProposal, PricingStage,Invoice,InvoiceItem,PhaseStatus,PhaseComment,SharedLink, ProposalChangeRequest,Notification
from flask_wtf import CSRFProtect
from datetime import datetime
from io import BytesIO
from flask import make_response, render_template
from xhtml2pdf import pisa
import uuid
from freelancer_models import (
    SharedLink,
    Meeting,
    Revision,
    Notification,
    db
)
from freelancer_models import Task,PricingStage
from flask_login import LoginManager, login_required, current_user
from flask import current_app

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'replace-with-a-secure-random-value'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        "mssql+pyodbc://SA:akash134@localhost/FreelancerDB"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager=LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
    # IMPORTANT: import your User model here to avoid circular imports
        from freelancer_models import User
        return User.query.get(int(user_id))
    # Create tables at startup
    return app 


app = create_app()
CSRFProtect(app) 

from datetime import datetime

@app.context_processor
def inject_now():
    # NOTE: we return the function itself, not its result
    return { 'now': datetime.utcnow }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = FreelancerRegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            role='freelancer'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('✅ Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            flash('✅ Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('❌ Invalid credentials.', 'danger')
    return render_template('login.html', form=form)


@app.route('/client/<int:client_id>')
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    projects = Project.query.filter_by(client_id=client_id).all()
    return render_template(
        'client_detail.html',
        client=client,
        projects=projects
    )


@app.route('/client/<int:client_id>/projects/add', methods=['GET','POST'])
def add_project(client_id):
    form = ProjectForm()
    if form.validate_on_submit():
        proj = Project(
          client_id=client_id,
          title=form.title.data,
          description=form.description.data,
          start_date=form.start_date.data,
          end_date=form.end_date.data,
          currency=form.currency.data
        )
        db.session.add(proj)
        db.session.commit()
        return redirect(url_for('client_detail', client_id=client_id))
    return render_template(
      'add_project.html',
      form=form,
      client=Client.query.get_or_404(client_id)
    )


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # 1) Must be logged in
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    # 2) Fetch the user record once and for all
    user = User.query.get(session['user_id'])
    if not user:
        flash("Session invalid—please log in again.", "warning")
        return redirect(url_for('login'))

    # 3) Handle the "Add Client" form
    form = ClientForm()
    csrf_form=CSRFOnlyForm()
    if form.validate_on_submit():
        new_client = Client(
            name        = form.name.data,
            email       = form.email.data,
            phone       = form.phone.data,
            notes       = form.notes.data,
            freelancer_id = user.id
        )
        db.session.add(new_client)
        db.session.commit()
        return redirect(url_for('dashboard'))

    # 4) Pull your dashboard stats
    clients = Client.query.filter_by(freelancer_id=user.id).all()
    total_clients  = len(clients)
    total_projects = (
        Project.query
               .filter(Project.client_id.in_([c.id for c in clients]))
               .count()
        if clients else 0
    )

    # 5) Finally render, passing in **user** (and everything else)
    return render_template(
        'dashboard.html',
        user=user,
        client_form=form,
        clients=clients,
        total_clients=total_clients,
        total_projects=total_projects
    )



from forms import PricingProposalForm

@app.route('/client/<int:client_id>/project/<int:project_id>')
def client_project_detail(client_id, project_id):
    project = Project.query.get_or_404(project_id)
    if project.client_id != client_id:
        abort(404)

    existing_proposals = PricingProposal.query \
        .filter_by(project_id=project_id) \
        .order_by(PricingProposal.id) \
        .all()

    # single form instance, used for both create/edit AND delete CSRF
    form = PricingProposalForm()
    csrf_form = CSRFOnlyForm()

    active_tab = request.args.get('tab', 'overview')
    return render_template(
        'project_detail.html',
        project=project,
        existing_proposals=existing_proposals,
        form=form,               # <- make sure this is here
        active_tab=active_tab,
        csrf_form=csrf_form
    )




@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            notes=form.notes.data,
            meeting_link=form.meeting_link.data,     # ← new field
            freelancer_id=session['user_id']
        )
        db.session.add(client)
        db.session.commit()
        flash("Client added!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_client.html', form=form)


from forms import ProfileForm

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Must be logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    # fetch current user
    user = User.query.get(session['user_id'])
    if not user:
        flash('Invalid session — please log in again.', 'danger')
        return redirect(url_for('login'))

    # instantiate the form, pre-populating name/email
    form = ProfileForm(
        name=user.name,
        email=user.email,
        education=user.education or '',
        Experience=user.Experience or '',
        linkedin=user.linkedin or ''
    )

    if form.validate_on_submit():
        # save back to the user
        user.education = form.education.data
        user.experience = form.experience.data
        user.linkedin = form.linkedin.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You've been logged out.", "info")
    return redirect(url_for('index'))


# PRICING ROUTES

@app.route('/project/<int:project_id>/pricing', methods=['POST'])
def pricing(project_id):
    project = Project.query.get_or_404(project_id)

    # 1) load or create the proposal
    prop_id = request.args.get('proposal_id', type=int)
    if prop_id:
        prop = PricingProposal.query.filter_by(id=prop_id, project_id=project_id).first_or_404()
    else:
        prop = PricingProposal.query.filter_by(project_id=project_id).first()
        if not prop:
            prop = PricingProposal(project_id=project_id)
            db.session.add(prop)

    # 2) bind + validate form
    form = PricingProposalForm(obj=prop)
    if not form.validate_on_submit():
        for fld, errs in form.errors.items():
            for e in errs:
                flash(f"{getattr(form, fld).label.text}: {e}", "danger")
        return redirect(url_for(
            'client_project_detail',
            client_id=project.client_id,
            project_id=project_id,
            tab='pricing',
            proposal_id=prop.id if prop.id else None
        ))

    # 3) copy top-level fields
    prop.type               = form.type.data
    prop.advanced_payment   = form.advanced_payment.data or 0
    prop.total_charge       = form.total_charge.data or 0
    prop.hourly_rate        = form.hourly_rate.data or 0
    prop.estimated_hours          = form.estimated_hours.data or 0
    prop.approved_by_client = False

    # 4) rebuild the stages Python list
    new_stages = []
    for idx, sd in enumerate(form.stages.data, start=1):
        details = sd.get('tech_details','').strip()
        if not details:
            continue
        new_stages.append(PricingStage(
            stage_number   = idx,
            tech_details   = details,
            deliverables   = sd.get('deliverables',''),
            amount         = sd.get('amount')  or 0,
            hours          = sd.get('hours')   or 0,
            due_date       = sd.get('due_date'),
            work_status    = sd.get('work_status','pending'),
            payment_status = sd.get('payment_status','pending'),
        ))

    # **this single line** tells SQLAlchemy:
    # “drop any old children, delete them from the DB, and replace with my new_stages[] list”
    prop.stages = new_stages

    # 5) commit
    db.session.commit()
    flash("✅ Pricing proposal saved!", "success")

    # 6) back to “view” tab
    return redirect(url_for(
        'client_project_detail',
        client_id=project.client_id,
        project_id=project_id,
        tab='view'
    ))


@app.route('/proposal/<int:proposal_id>/approve', methods=['POST'])
def approve_proposal_globally(proposal_id):
    prop = PricingProposal.query.get_or_404(proposal_id)
    prop.approved_by_client = True
    db.session.commit()
    return redirect(url_for(
        'client_project_detail',
        client_id=prop.project.client_id,
        project_id=prop.project_id,
        tab='view'
    ))




@app.route('/project/<int:project_id>/pricing/view')
def pricing_view(project_id):
    project = Project.query.get_or_404(project_id)
    proposal = PricingProposal.query.filter_by(project_id=project_id).first()
    
    if not proposal:
        flash('No pricing proposal found for this project.', 'warning')
        return redirect(url_for('project_detail', project_id=project_id))
    change_requests = proposal.change_requests
    return render_template(
        'pricing_view.html',
        project=project,
        proposal=proposal,
        change_requests=change_requests
    )


@app.route('/project/<int:project_id>/proposal/<int:proposal_id>/approve', methods=['POST'])
def approve_proposal_for_project(project_id, proposal_id):
    proposal = PricingProposal.query.get_or_404(proposal_id)
    if proposal.project_id != project_id:
        abort(404)
    
    proposal.approved_by_client = True
    db.session.commit()
    flash('✅ Proposal approved by client!', 'success')
    return redirect(url_for('client_project_detail', 
                          client_id=proposal.project.client_id, 
                          project_id=project_id, 
                          tab='view'))
@app.route('/proposal/<int:proposal_id>/delete', methods=['POST'])
def delete_proposal(proposal_id):
    prop = PricingProposal.query.get_or_404(proposal_id)

    # read the scalars before we delete/commit
    project_id = prop.project_id
    client_id  = prop.project.client_id   # this *will* lazy load, but session is still live here

    db.session.delete(prop)
    db.session.commit()

    return redirect(url_for(
        'client_project_detail',
        client_id=client_id,
        project_id=project_id,
        tab='view'
    ))
@app.route('/client/<int:client_id>/delete', methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    # you may want to cascade/delete all projects for that client, or forbid it
    db.session.delete(client)
    db.session.commit()
    flash(f"Client “{client.name}” deleted.", "success")
    return redirect(url_for('dashboard'))
@app.route('/client/<int:client_id>/project/<int:project_id>/delete', methods=['POST'])
def delete_project(client_id, project_id):
    project = Project.query.get_or_404(project_id)
    if project.client_id != client_id:
        abort(404)
    db.session.delete(project)
    db.session.commit()
    flash(f"Project “{project.title}” deleted.", "success")
    return redirect(url_for('client_detail', client_id=client_id))

# —— wiring CSRF form into all your listing views ——
@app.context_processor
def inject_csrf_form():
    return { 'csrf_form': CSRFOnlyForm() }

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)   # pre-populate with existing data

    if form.validate_on_submit():
        form.populate_obj(client)    # copy form fields back onto client
        db.session.commit()
        flash(f'Client "{client.name}" updated.', 'success')
        return redirect(url_for('client_detail', client_id=client.id))

    return render_template('edit_client.html', form=form, client=client)


@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        form.populate_obj(project)
        db.session.commit()
        flash(f'Project "{project.title}" updated.', 'success')
        return redirect(url_for('client_project_detail', client_id=project.client_id,project_id=project.id))

    return render_template('edit_project.html', form=form, project_id=project.id,project_title=project.title,client_id=project.client_id)

@app.route(
  '/client/<int:client_id>/project/<int:project_id>/proposal/<int:prop_id>/invoice',
  methods=['GET','POST']
)
def invoice_form(client_id, project_id, prop_id):
    client   = Client.query.get_or_404(client_id)
    project  = Project.query.get_or_404(project_id)
    proposal = PricingProposal.query.get_or_404(prop_id)

    # Handle POST: save or update
    if request.method == 'POST':
        # collect stage names & costs
        names = request.form.getlist('stage_name[]')
        costs = request.form.getlist('stage_cost[]')
        adv   = request.form['advance_payment']

        # either create new or fetch existing
        inv_id = request.form.get('invoice_id')
        if inv_id:
            invoice = Invoice.query.get(inv_id)
            # clear existing items
            invoice.items.clear()
        else:
            invoice = Invoice(
              proposal_id=proposal.id,
              created_at=datetime.utcnow()
            )
            db.session.add(invoice)

        invoice.advance_paid = adv
        # add new items
        for idx, (n,c) in enumerate(zip(names, costs), start=1):
            invoice.items.append(
              InvoiceItem(
                invoice=invoice,
                stage_no=idx,
                name=n,
                cost=c
              )
            )

        # recalc totals
        invoice.total_cost = sum(float(c) for c in costs)
        invoice.amount_due = invoice.total_cost - float(adv)

        db.session.commit()
        flash('Invoice saved.', 'success')
        # now invoice.id exists
        return redirect(
          url_for('invoice_form',
                  client_id=client_id,
                  project_id=project_id,
                  prop_id=prop_id,
                  invoice_id=invoice.id)
        )

    # GET: pick up invoice_id from querystring if present
    invoice_id = request.args.get('invoice_id', type=int)

    return render_template(
      'invoice_form.html',
      client=client,
      project=project,
      proposal=proposal,
      csrf_form=CSRFOnlyForm(),
      now=datetime.utcnow(),
      invoice_id=invoice_id
    )
from flask import make_response, render_template


def render_pdf(html: str) -> bytes:
    """Convert HTML to PDF bytes using xhtml2pdf."""
    result = BytesIO()
    # pisa.CreatePDF writes the PDF into 'result'
    pisa_status = pisa.CreatePDF(src=html, dest=result)
    if pisa_status.err:
        raise RuntimeError('Error generating PDF')
    return result.getvalue()

@app.route('/download_invoice/<int:invoice_id>')
def download_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Render your invoice as HTML (reuse invoice_pdf.html or similar)
    html = render_template('invoice_pdf.html', invoice=invoice)
    try:
        pdf_data = render_pdf(html)
    except RuntimeError:
        abort(500, description="PDF generation failed")

    response = make_response(pdf_data)
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = (
        f'inline; filename=invoice_{invoice.id}.pdf'
    )
    return response


@app.route(
  '/client/<int:client_id>/project/<int:project_id>/tracking',
  methods=['GET','POST'])
def project_tracking(client_id, project_id):
    client  = Client.query.get_or_404(client_id)
    project = Project.query.get_or_404(project_id)

    # only track the approved proposal
    proposal = PricingProposal.query.filter_by(
        project_id=project.id,
        approved_by_client=True
    ).first()
    if not proposal:
        flash('No approved proposal found to track.', 'warning')
        return redirect(url_for(
            'client_project_detail',
            client_id=client_id,
            project_id=project_id,
            tab='view'
        ))

    stages = proposal.stages
    phases = ['Planning', 'Execution', 'Review']

    # Build dicts of statuses & comments
    statuses = {}
    comments = {}
    for stage in stages:
        statuses[stage.id] = {}
        comments[stage.id] = {}
        for ph in phases:
            ps = PhaseStatus.query.filter_by(
                stage_id=stage.id,
                phase=ph
            ).first()
            statuses[stage.id][ph] = ps.status if ps else 'Pending'

            comments[stage.id][ph] = PhaseComment.query.filter_by(
                stage_id=stage.id,
                phase=ph
            ).order_by(PhaseComment.created_at).all()
     # 1) upcoming meetings
    meetings = Meeting.query.filter_by(project_id=project.id)\
                            .order_by(Meeting.when).all()

    # 2) revisions (all revisions for this project’s meetings)
    revisions = Revision.query.join(Meeting)\
                     .filter(Meeting.project_id == project.id)\
                     .order_by(Revision.created_at.desc()).all()

    # 3) invoices
    invoices = Invoice.query.filter_by(proposal_id=proposal.id)\
                    .order_by(Invoice.created_at.desc()).all()

    # 4) notifications
    notifications = Notification.query.filter_by(project_id=project.id)\
                             .order_by(Notification.created_at.desc()).all()
    return render_template(
        'project_tracking.html',
        client=client,
        project=project,
        stages=stages,
        phases=phases,
        statuses=statuses,
        comments=comments,
        meetings=meetings,
      revisions=revisions,
      invoices=invoices,
      notifications=notifications,
        csrf_form=CSRFOnlyForm(),
        proposal=proposal,
        project_id=project.id
    )

@app.route('/revisions/<int:rev_id>/toggle', methods=['POST'])
def toggle_revision(rev_id):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400, "Bad request")
    rev = Revision.query.get_or_404(rev_id)
    # flip the flag
    rev.is_paid = not rev.is_paid
    db.session.commit()
    flash(
        f"Revision #{rev.id} marked “{'Complete' if rev.is_paid else 'Pending'}”.",
        "success"
    )
    # go back to the tracker page you came from
    return redirect(request.referrer or url_for(
        'project_tracking',
        client_id=rev.project.client_id,
        project_id=rev.project_id
    ))
@app.route('/phase/status', methods=['POST'])
def update_phase_status():
    stage_id = request.form.get('stage_id', type=int)
    phase    = request.form.get('phase')
    if not stage_id or not phase:
        flash("Invalid phase status request", "danger")
        return redirect(request.referrer or url_for('dashboard'))

    # find or create the PhaseStatus row
    ps = PhaseStatus.query.filter_by(
        stage_id=stage_id,
        phase=phase
    ).first()
    if not ps:
        ps = PhaseStatus(stage_id=stage_id, phase=phase, status='Complete')
        db.session.add(ps)
    else:
        # toggle between Pending/Complete
        ps.status = 'Complete' if ps.status!='Complete' else 'Pending'

    db.session.commit()

    # redirect back to the tracker view
    stage    = PricingStage.query.get_or_404(stage_id)
    proj     = stage.proposal.project
    return redirect(url_for(
        'project_tracking',
        client_id=proj.client_id,
        project_id=proj.id
    ))


# Add a comment to a phase
@app.route('/phase/comment', methods=['POST'])
def add_phase_comment():
    stage_id = request.form.get('stage_id', type=int)
    phase    = request.form.get('phase')
    content  = request.form.get('comment','').strip()

    if not all([stage_id, phase, content]):
        flash("Please enter a comment.", "warning")
        return redirect(request.referrer or url_for('dashboard'))

    comment = PhaseComment(
        stage_id=stage_id,
        phase=phase,
        content=content
    )
    db.session.add(comment)
    db.session.commit()

    # redirect back to the tracker view
    stage    = PricingStage.query.get_or_404(stage_id)
    proj     = stage.proposal.project
    return redirect(url_for(
        'project_tracking',
        client_id=proj.client_id,
        project_id=proj.id
    ))
from datetime import datetime

@app.route('/shared/<string:token>', methods=['GET'])
def client_dashboard(token):
    link = SharedLink.query.filter_by(token=token, is_active=True).first_or_404()
    project  = link.project

    # 1) load the most recent proposal
    proposal = (PricingProposal.query
                    .filter_by(project_id=project.id)
                    .order_by(PricingProposal.id.desc())
                    .first_or_404("No proposal exists yet"))

    # 2) your phases + statuses + comments as before
    phases   = ['Planning', 'Execution', 'Review']
    stages   = proposal.stages

    statuses = {
      stage.id: {
        ph: (ps := PhaseStatus.query
                  .filter_by(stage_id=stage.id, phase=ph)
                  .first()) and ps.status or 'Pending'
        for ph in phases
      }
      for stage in stages
    }
    comments = {
      stage.id: {
        ph: PhaseComment.query
                    .filter_by(stage_id=stage.id, phase=ph)
                    .order_by(PhaseComment.created_at)
                    .all()
        for ph in phases
      }
      for stage in stages
    }

    # 3) load upcoming meetings (only future ones)
    now = datetime.utcnow()
    meetings = (Meeting.query
                     .filter_by(project_id=project.id)
                     .filter(Meeting.when >= now)
                     .order_by(Meeting.when)
                     .all())

    # 4) load notifications (all, newest first)
    notifications = (Notification.query
                           .filter_by(project_id=project.id)
                           .order_by(Notification.created_at.desc())
                           .all())

    # 5) load revisions + invoices
    revisions = Revision.query.filter(Revision.meeting_id.in_([ m.id for m in meetings ])).order_by(Revision.created_at.desc()).all()
    invoices  = Invoice.query.filter_by(proposal_id=proposal.id).order_by(Invoice.created_at.desc()).all()

    return render_template(
      'client_dashboard.html',
      link=link,
      project=project,
      proposal=proposal,
      phases=phases,
      stages=stages,
      statuses=statuses,
      comments=comments,
      meetings=meetings,
      notifications=notifications,
      revisions=revisions,
      invoices=invoices,
      csrf_form=CSRFOnlyForm(),
    )



@app.route('/stage/payment', methods=['POST'], endpoint='update_stage_payment')
def update_stage_payment():
    stage_id = request.form.get('stage_id', type=int)
    stage    = PricingStage.query.get_or_404(stage_id)

    # toggle between 'pending' and 'complete'
    stage.payment_status = (
        'complete' if stage.payment_status != 'complete' else 'pending'
    )
    db.session.commit()

    proj = stage.proposal.project
    return redirect(url_for(
        'project_tracking',
        client_id=proj.client_id,
        project_id=proj.id
    ))

@app.route('/project/<int:project_id>/share', methods=['POST'])
def toggle_shared_link(project_id):
    # load the project
    project = Project.query.get_or_404(project_id)

    # get (or create) the one SharedLink for this project
    link = SharedLink.query.filter_by(project_id=project.id).first()
    if link is None:
        # first time: generate and activate a new token
        link = SharedLink(
            project_id=project.id,
            token=uuid.uuid4().hex,
            is_active=True
        )
        db.session.add(link)
        flash('Share link created! Copy the URL below.', 'success')
    else:
        # toggle on/off
        link.is_active = not link.is_active
        verb = 'deactivated' if not link.is_active else 'reactivated'
        flash(f'Share link {verb}.', 'info')

    db.session.commit()

    # back to the same project page
    return redirect(url_for(
        'client_project_detail',
        client_id=project.client_id,
        project_id=project.id,
        tab='overview'
    ))

from flask import request, flash, redirect, url_for, abort

@app.route('/shared/<string:token>/approve/<int:proposal_id>', methods=['POST'])
def client_approve_proposal(token, proposal_id):
    link = SharedLink.query.filter_by(token=token, is_active=True).first_or_404()
    proposal = PricingProposal.query.get_or_404(proposal_id)
    # ensure the proposal actually belongs to this shared project
    if proposal.project_id != link.project_id:
        abort(403)
    proposal.approved_by_client = True
    db.session.commit()
    flash('✅ Proposal approved!', 'success')
    return redirect(url_for('client_dashboard', token=token))

@app.route('/client_request_change/<int:proposal_id>/<string:token>',
           methods=['POST'])
def client_request_change(proposal_id, token):
    form = CSRFOnlyForm()
    if form.validate_on_submit():
        # grab the message
        msg = request.form.get('message','').strip()
        if msg:
            cr = ProposalChangeRequest(
                proposal_id=proposal_id,
                content=msg
            )
            db.session.add(cr)
            db.session.commit()
            flash('✏️ Your change request has been sent.', 'success')
    return redirect(
      url_for('client_dashboard', token=token)
    )
@app.route('/project/<int:project_id>/schedule', methods=['POST'])
def schedule_meeting(project_id):
    # 0) CSRF check
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400, "Bad request")

    # 1) Load the project
    project = Project.query.get_or_404(project_id)

    # 2) Parse form inputs
    #    HTML datetime-local gives "YYYY-MM-DDTHH:MM"
    when_iso = request.form.get('when', '')
    agenda   = request.form.get('agenda', '').strip()

    try:
        when = datetime.fromisoformat(when_iso)
    except ValueError:
        abort(400, "Invalid date/time")

    # 3) Create the Meeting
    meeting = Meeting(
        project_id=project.id,
        when=when,
        agenda=agenda
    )
    db.session.add(meeting)

    # 4) Create a Notification
    notif = Notification(
        project_id=project.id,
        text=f"New meeting scheduled on {when.strftime('%Y-%m-%d %H:%M')}"
    )
    db.session.add(notif)

    # 5) Commit both in one transaction
    db.session.commit()

    flash("🗓️ Meeting scheduled!", "success")

    # 6) Redirect back to whichever page the user was on
    return redirect(request.referrer or 
                    url_for('project_tracking', 
                            client_id=project.client_id, 
                            project_id=project.id))

from flask import request, redirect, flash
from datetime import datetime

@app.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400)
    n = Notification.query.get_or_404(notif_id)
    n.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

# — cancel a meeting —
@app.route('/meetings/<int:meeting_id>/cancel', methods=['POST'])
def cancel_meeting(meeting_id):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400)
    m = Meeting.query.get_or_404(meeting_id)
    db.session.delete(m)
    db.session.commit()
    flash("🗑️ Meeting canceled", "success")
    return redirect(
        request.referrer
        or url_for('project_tracking',
                   client_id=m.project.client_id,
                   project_id=m.project_id,meeting_id=m.meeting_id)
    )



# — delete a phase comment —
@app.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400)
    c = PhaseComment.query.get_or_404(comment_id)
    db.session.delete(c)
    db.session.commit()
    flash("🗑 Note deleted", "success")
    return redirect(request.referrer or url_for('project_tracking',
                                               client_id=c.stage.proposal.project.client_id,
                                               project_id=c.stage.proposal.project_id))

# — add a revision —
@app.route('/projects/<int:project_id>/revisions', methods=['POST'])
def revision_request(project_id):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        abort(400)

    # optional meeting
    meeting_id = request.form.get('meeting_id', type=int) or None
    notes      = request.form['notes']
    cost       = request.form.get('cost', type=float, default=0.0)
    is_paid    = bool(request.form.get('is_paid'))

    # NOW we supply project_id from the URL
    rev = Revision(
        project_id=project_id,
        meeting_id=meeting_id,
        notes=notes,
        cost=cost,
        is_paid=is_paid
    )

    db.session.add(rev)
    db.session.commit()

    # redirect back to your tracking page
    project = Project.query.get_or_404(project_id)
    return redirect(url_for(
        'project_tracking',
        client_id=project.client_id,
        project_id=project_id
    ))

# — delete a revision —



@app.route(
  '/projects/<int:project_id>/revisions/<int:rev_id>/delete',
  methods=['POST']
)
def delete_revision(project_id, rev_id):
    # ensure the revision exists and belongs to this project
    rev = Revision.query.filter_by(
        id=rev_id,
        project_id=project_id
    ).first_or_404()

    db.session.delete(rev)
    db.session.commit()
    flash("🗑️ Revision deleted", "info")

    # redirect you back to the tracking page
    proj = Project.query.get_or_404(project_id)
    return redirect(url_for(
        'project_tracking',
        client_id=proj.client_id,
        project_id=project_id
    ))

@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    t = Task.query.get_or_404(task_id)
    stage = PricingStage.query.get_or_404(t.pricing_stage_id)
    project = Project.query.get_or_404(stage.project_id)
    if project.freelancer_id != current_user.id:
        abort(403)

    t.is_done = not t.is_done
    db.session.commit()
    return jsonify({'id': t.id, 'is_done': t.is_done}), 200

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    t = Task.query.get_or_404(task_id)
    stage = PricingStage.query.get_or_404(t.pricing_stage_id)
    project = Project.query.get_or_404(stage.project_id)
    if project.client_id != current_user.id:
        abort(403)

    db.session.delete(t)
    db.session.commit()
    return jsonify({'id': task_id}), 200


@app.route('/tasks/create', methods=['POST'])
@login_required
def add_task():
    # 1) Grab raw form values
    raw_stage   = request.form.get('stage_id', '').strip()
    raw_project = request.form.get('project_id', '').strip()

    # 2) Validate they're nonempty & integers
    if not raw_stage or not raw_stage.isdigit():
        return jsonify({'error': 'stage_id is required and must be an integer'}), 400
    if not raw_project or not raw_project.isdigit():
        return jsonify({'error': 'project_id is required and must be an integer'}), 400

    stage_id   = int(raw_stage)
    project_id = int(raw_project)

    # 3) Fetch the stage and ensure it belongs to this project
    stage = PricingStage.query.get_or_404(stage_id)
    proposal = stage.proposal
    if proposal.project_id != project_id:
        return jsonify({'error': 'Stage does not belong to this project'}), 400

    # 4) Now verify the current_user really is the freelancer on that project:
    project = Project.query.get_or_404(project_id)
    # (Assuming “project.client.freelancer_id” is a valid relationship)
    if project.client.freelancer_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403

    # 5) Grab & validate “description”
    description = request.form.get('description', '').strip()
    if not description:
        return jsonify({'error': 'Description cannot be empty'}), 400

    # 6) Parse optional dates
    raw_start = request.form.get('start_date', '').strip()
    raw_end   = request.form.get('end_date', '').strip()
    remarks   = request.form.get('remarks', '').strip()

    try:
        start_date = datetime.strptime(raw_start, '%Y-%m-%d').date() if raw_start else None
    except ValueError:
        return jsonify({'error': 'Invalid start_date format'}), 400
    try:
        end_date = datetime.strptime(raw_end, '%Y-%m-%d').date() if raw_end else None
    except ValueError:
        return jsonify({'error': 'Invalid end_date format'}), 400

    # 7) Create & commit the Task
    new_task = Task(
        stage_id=stage_id,
        description=description,
        start_date=start_date,
        end_date=end_date,
        remarks=remarks,
        is_done=False
    )
    db.session.add(new_task)
    db.session.commit()

    # 8) Return a 201 JSON response
    return jsonify({
        'id': new_task.id,
        'description': new_task.description,
        'start_date': new_task.start_date.isoformat() if new_task.start_date else '',
        'end_date': new_task.end_date.isoformat() if new_task.end_date else '',
        'remarks': new_task.remarks or ''
    }), 201


if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint:20s} -> {rule.rule}")
    app.run(debug=True)


