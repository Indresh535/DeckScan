<%@ Page Title="About" Language="C#" MasterPageFile="~/Site.Master" AutoEventWireup="true" CodeBehind="About.aspx.cs" Inherits="ImgeScan.About" %>

<asp:Content ID="BodyContent" ContentPlaceHolderID="MainContent" runat="server">
     <div>
            <asp:FileUpload ID="FileUpload1" runat="server" />
            <asp:Button ID="Scan" runat="server" Text="Upload and Scan" OnClick="Scan_Click"/>
            <asp:Image ID="Image1" runat="server" Visible="false" />
            <asp:GridView ID="GridView1" runat="server" AutoGenerateColumns="False">
                <Columns>
                    <asp:BoundField DataField="CabinNo" HeaderText="Cabin Number" />
                    <asp:BoundField DataField="Category" HeaderText="Category" />
                    <asp:BoundField DataField="CabinTypeException" HeaderText="Cabin Type Exception" />
                    <asp:BoundField DataField="Coordinates" HeaderText="Coordinates" />
                </Columns>
            </asp:GridView>
        </div>

</asp:Content>
