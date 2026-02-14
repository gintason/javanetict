from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
import json
import io
from datetime import datetime, timedelta
from django.conf import settings
import os
from reportlab.platypus import Image


# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus.flowables import HRFlowable

from .models import ProposalRequest
from .serializers import ProposalRequestSerializer

class ProposalRequestListView(generics.ListAPIView):
    """List proposal requests (admin only)"""
    queryset = ProposalRequest.objects.all().order_by('-created_at')
    serializer_class = ProposalRequestSerializer
    permission_classes = [permissions.IsAdminUser]

class ProposalRequestDetailView(generics.RetrieveAPIView):
    """Get specific proposal request"""
    queryset = ProposalRequest.objects.all()
    serializer_class = ProposalRequestSerializer
    permission_classes = [permissions.IsAdminUser]

class GenerateProposalView(APIView):
    """Generate a new proposal with deployment fee calculation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'email', 'institution', 'country']
            for field in required_fields:
                if not data.get(field):
                    return Response({
                        'status': 'error',
                        'message': f'{field} is required'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate deployment fee
            country = data.get('country', '').lower()
            needs_ctb = data.get('needs_ctb', False)
            needs_live_classes = data.get('needs_live_classes', False)
            estimated_students = data.get('estimated_students', 100)
            
            # Calculate fee
            if country in ['nigeria', 'ghana', 'kenya', 'south africa']:
                base = 5000000  # ₦5 million
                if needs_ctb and needs_live_classes:
                    base += 2000000
                if estimated_students > 1000:
                    base += 2000000
                elif estimated_students > 500:
                    base += 1000000
                amount = f"₦{base:,}"
                currency = "NGN"
                currency_symbol = "₦"
            else:
                base = 10000  # $10,000
                if needs_ctb and needs_live_classes:
                    base += 3000
                amount = f"${base:,}"
                currency = "USD"
                currency_symbol = "$"
            
            # Create proposal data for serializer
            proposal_data = {
                'name': data.get('name'),
                'email': data.get('email'),
                'institution': data.get('institution'),
                'phone': data.get('phone', ''),
                'country': data.get('country'),
                'needs_ctb': needs_ctb,
                'needs_live_classes': needs_live_classes,
                'estimated_students': estimated_students,
                'estimated_teachers': data.get('estimated_teachers', 10),
                'preferred_colors': data.get('preferred_colors', ''),
                'has_logo': data.get('has_logo', False),
                'currency': currency,
                'deployment_fee': amount,
                'status': 'GENERATED'  # Override serializer's default
            }
            
            # Create proposal using serializer
            serializer = ProposalRequestSerializer(data=proposal_data)
            if serializer.is_valid():
                proposal = serializer.save()
                
                # Prepare response matching your TypeScript interface
                response_data = {
                    'status': 'success',
                    'message': 'Proposal generated successfully',
                    'proposal_id': str(proposal.id),  # Convert UUID to string
                    'deployment_fee': {
                        'amount': amount,
                        'currency': currency,
                        'currency_symbol': currency_symbol,
                        'range': f'{amount} - {amount}',
                        'note': 'One-time deployment fee'
                    },
                    'data': {
                        'id': proposal.id,
                        'name': proposal.name,
                        'email': proposal.email,
                        'institution': proposal.institution,
                        'phone': proposal.phone,
                        'country': proposal.country,
                        'currency': currency,
                        'deployment_fee': amount,
                        'created_at': proposal.created_at.isoformat(),
                        'needs_ctb': proposal.needs_ctb,
                        'needs_live_classes': proposal.needs_live_classes,
                        'estimated_students': proposal.estimated_students,
                        'estimated_teachers': proposal.estimated_teachers,
                        'preferred_colors': proposal.preferred_colors,
                        'has_logo': proposal.has_logo
                    }
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class GenerateProposalPDFView(APIView):
    """Generate PDF proposal with company letterhead"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            # SIMPLIFIED: Just log basic info
            print("=" * 60)
            print("📥 PDF GENERATION REQUEST")
            print(f"Method: {request.method}")
            print(f"Path: {request.path}")
            print("=" * 60)
            
            data = request.data
            proposal_id = data.get('proposal_id')
            
            # Simple debug of data
            print(f"Has proposal_id: {'proposal_id' in data}")
            print(f"Keys in data: {list(data.keys())}")
            
            # Handle deployment fee - SIMPLIFIED
            deployment_fee = 'N/A'
            if 'deployment_fee' in data:
                if isinstance(data['deployment_fee'], dict):
                    deployment_fee = data['deployment_fee'].get('amount', 'N/A')
                else:
                    deployment_fee = data['deployment_fee']
            
            print(f"Deployment fee: {deployment_fee}")
            
            # Build pdf_data - SIMPLIFIED
            pdf_data = {
                'proposal_id': proposal_id or f"TEMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'institution': data.get('institution', ''),
                'phone': data.get('phone', ''),
                'country': data.get('country', ''),
                'needs_ctb': data.get('needs_ctb', False),
                'needs_live_classes': data.get('needs_live_classes', False),
                'estimated_students': data.get('estimated_students', 0),
                'estimated_teachers': data.get('estimated_teachers', 0),
                'preferred_colors': data.get('preferred_colors', ''),
                'has_logo': data.get('has_logo', False),
                'deployment_fee': deployment_fee
            }
            
            institution = data.get('institution', 'Unknown')
            
            print(f"Creating PDF for: {institution}")
            
            # Create PDF
            buffer = io.BytesIO()
            
            try:
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=20*mm,
                    leftMargin=20*mm,
                    topMargin=25*mm,
                    bottomMargin=20*mm
                )
                
                # Build PDF content
                story = self._create_pdf_content(pdf_data)
                doc.build(story)
                
            except Exception as pdf_error:
                print(f"❌ PDF creation error: {str(pdf_error)}")
                raise pdf_error
            
            # Get PDF bytes
            pdf = buffer.getvalue()
            buffer.close()
            
            if len(pdf) < 100:
                raise ValueError(f"PDF too small ({len(pdf)} bytes)")
            
            print(f"✅ PDF created: {len(pdf)} bytes")
            
            # Create Django HttpResponse
            response = HttpResponse(
                pdf,
                content_type='application/pdf'
            )
            
            # Generate filename
            institution_safe = institution.replace(' ', '_')
            proposal_id_str = str(proposal_id) if proposal_id else 'temp'
            filename = f"Proposal_{proposal_id_str}_{institution_safe}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return simple JSON error
            return Response({
                'status': 'error',
                'message': f'Error generating PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    def _create_pdf_content(self, data):
        """Create PDF content elements - SINGLE VERSION (remove duplicates)"""
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0d6efd'),
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=5
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=5,
            fontName='Helvetica'
        )
        
        # ===========================================
        # 1. LETTERHEAD WITH 350x350 LOGO
        # ===========================================
        try:
            from reportlab.platypus import Image
            
            # YOUR ACTUAL LOGO PATH
            logo_path = "static/images/logo/paperlogo.png"
            
            try:
                # Load the 350x350 logo
                logo_image = Image(logo_path, width=180, height=150)
                print(f"✅ Logo loaded successfully from: {logo_path}")
                
                # Center the logo
                logo_image.hAlign = 'CENTER'
                story.append(logo_image)
                story.append(Spacer(1, 2))  # Small space after logo
                
                
            except Exception as img_error:
                # If logo file not found or can't be read
                print(f"⚠️ Could not load logo from {logo_path}: {img_error}")
                print("Using text fallback...")
                story.append(Paragraph("JAVANET ICT SOLUTIONS", title_style))
                
        except ImportError:
            # If Image import fails
            print("⚠️ ReportLab Image import failed. Using text fallback.")
            story.append(Paragraph("PROFESSIONAL E-LEARNING PLATFORM DEPLOYMENT", title_style))
        
        # Company tagline
        story.append(Paragraph("", 
                            ParagraphStyle('SubTitle', parent=styles['Normal'], 
                                        fontSize=12, alignment=TA_CENTER,
                                        textColor=colors.HexColor('#666666'))))
        
        # Company contact info
        company_info = [
            "House 26, T.O.S Benson Crescent, Utako, Abuja, Nigeria",
            "Phone: +234 703 067 3089 | Email: info@javanetict.com",
            "Website: www.javanetict.com"
        ]
        
        for line in company_info:
            story.append(Paragraph(line, company_style))
        
        story.append(Spacer(1, 10))
        
        # Horizontal line
        story.append(HRFlowable(width="100%", thickness=1, 
                            color=colors.HexColor('#0d6efd'),
                            spaceBefore=5, spaceAfter=15))
        
        # ===========================================
        # 2. PROPOSAL HEADER
        # ===========================================
        current_date = datetime.now()
        expiry_date = current_date + timedelta(days=30)
        proposal_id = data.get('proposal_id', 'temp')
        
        header_data = [
            ["PROPOSAL ID", f"#{proposal_id}"],
            ["DATE", current_date.strftime("%B %d, %Y")],
            ["VALID UNTIL", expiry_date.strftime("%B %d, %Y")]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0d6efd')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 25))
        
        # ===========================================
        # 3. RECIPIENT INFO
        # ===========================================
        story.append(Paragraph("TO:", heading_style))
        recipient_info = f"""
        <b>{data.get('name', '')}</b><br/>
        {data.get('institution', '')}<br/>
        {data.get('country', '')}<br/>
        Email: {data.get('email', '')}<br/>
        Phone: {data.get('phone', 'Not provided')}
        """
        story.append(Paragraph(recipient_info, normal_style))
        story.append(Spacer(1, 25))
        
        # ===========================================
        # 4. MAIN TITLE
        # ===========================================
        story.append(Paragraph("CUSTOM E-LEARNING PLATFORM DEPLOYMENT PROPOSAL", 
                            ParagraphStyle('MainTitle', parent=styles['Heading1'],
                                        fontSize=16, alignment=TA_CENTER,
                                        textColor=colors.HexColor('#0d6efd'),
                                        spaceAfter=15, fontName='Helvetica-Bold')))
        
        story.append(HRFlowable(width="60%", thickness=2, 
                            color=colors.HexColor('#0d6efd'),
                            spaceBefore=5, spaceAfter=20))
        
        # ===========================================
        # 5. EXECUTIVE SUMMARY
        # ===========================================
        story.append(Paragraph("1. EXECUTIVE SUMMARY", heading_style))
        
        summary_text = f"""
        This formal proposal outlines the comprehensive one-time deployment package for a 
        customized e-learning platform tailored specifically for <b>{data.get('institution', '')}</b> 
        located in <b>{data.get('country', '')}</b>. The proposed solution is designed to 
        support approximately <b>{data.get('estimated_students', 0)}</b> students and 
        <b>{data.get('estimated_teachers', 0)}</b> teachers.
        """
        
        story.append(Paragraph(summary_text, normal_style))
        story.append(Spacer(1, 25))
        
        # ===========================================
        # 6. DEPLOYMENT FEE
        # ===========================================
        story.append(Paragraph("2. ONE-TIME DEPLOYMENT FEE", heading_style))
        
        fee_amount = data.get('deployment_fee', 'N/A')
        fee_paragraph = Paragraph(f"""
        <para alignment="center">
        <font size="20" color="#198754"><b>{fee_amount}</b></font><br/>
        <font size="9" color="#666666">No Monthly Fees • Complete Ownership • Source Code Included</font>
        </para>
        """, normal_style)
        
        story.append(fee_paragraph)
        story.append(Spacer(1, 25))
        
        # ===========================================
        # 7. MODULES INCLUDED
        # ===========================================
        story.append(Paragraph("3. PLATFORM MODULES INCLUDED", heading_style))
        
        needs_ctb = data.get('needs_ctb', False)
        needs_live = data.get('needs_live_classes', False)
        
        if needs_ctb:
            story.append(Paragraph("✓ Computer-Based Testing (CBT) System", 
                                ParagraphStyle('ModuleTitle', parent=styles['Normal'],
                                            fontSize=11, textColor=colors.HexColor('#0d6efd'),
                                            leftIndent=15, fontName='Helvetica-Bold')))
            cbt_features = [
                "• Advanced question bank management system",
                "• Automated grading and analytics dashboard",
                "• Secure, Role-Based Authentication",
                "• Multi-format question support"
            ]
            for feature in cbt_features:
                story.append(Paragraph(feature, 
                                    ParagraphStyle('Feature', parent=styles['Normal'],
                                                fontSize=9, leftIndent=30)))
            story.append(Spacer(1, 12))
        
        if needs_live:
            story.append(Paragraph("✓ Live Interactive Classroom", 
                                ParagraphStyle('ModuleTitle', parent=styles['Normal'],
                                            fontSize=11, textColor=colors.HexColor('#198754'),
                                            leftIndent=15, fontName='Helvetica-Bold')))
            live_features = [
                "• HD video conferencing with virtual whiteboard",
                "• Intelligent Matching Engine",
                "• Smart Attendance & Payroll",
                "• Teacher Recruitment Suite"
            ]
            for feature in live_features:
                story.append(Paragraph(feature, 
                                    ParagraphStyle('Feature', parent=styles['Normal'],
                                                fontSize=9, leftIndent=30)))
            story.append(Spacer(1, 25))
        
        # ===========================================
        # 8. SCOPE OF WORK
        # ===========================================
        story.append(Paragraph("4. SCOPE OF DEPLOYMENT", heading_style))
        
        scope_items = [
            "• Custom platform branding with institution's colors and logo",
            "• Complete source code transfer and ownership rights",
            "• Full installation and configuration on your servers",
            "• Administrator and teacher training sessions",
            "• One year of comprehensive technical support",
            "• Lifetime system updates and security patches"
        ]
        
        for item in scope_items:
            story.append(Paragraph(item, normal_style))
        
        story.append(Spacer(1, 35))
        
        # ===========================================
        # 9. FOOTER WITH SIGNATURE
        # ===========================================
        
        # Get the path to your signature image
        signature_path = os.path.join(settings.BASE_DIR, 'static/images/signature.png')
        
        # Check if signature file exists and create appropriate cell
        signature_cell = None
        if os.path.exists(signature_path):
            try:
                signature_cell = Image(signature_path, width=120, height=40)
                print(f"✅ Signature loaded successfully from: {signature_path}")
            except Exception as sig_error:
                print(f"⚠️ Could not load signature from {signature_path}: {sig_error}")
                signature_cell = "_________________________"
        else:
            print(f"⚠️ Signature file not found at: {signature_path}")
            signature_cell = "_________________________"
        
        footer_data = [
            ["JAVANET ICT SOLUTIONS", "PROPOSAL VALID FOR 30 DAYS", "AUTHORIZED SIGNATURE"],
            ["Building Digital Learning Ecosystems", 
            f"Issue Date: {current_date.strftime('%B %d, %Y')}", 
            signature_cell],  # Use signature image here
            ["Transforming Education Through Technology", 
            f"Expiry: {expiry_date.strftime('%B %d, %Y')}", 
            "CEO, JAVANET ICT SOLUTIONS LTD"]
        ]
        
        footer_table = Table(footer_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(footer_table)
        
        return story