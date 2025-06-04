import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Set page config
st.set_page_config(
    page_title="MHT CET College Finder",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data function
@st.cache_data
def load_data():
    """Load and prepare data for the application"""
    # Try CSV first (faster for large datasets)
    if os.path.exists("mht_cet_cutoffs.csv"):
        df = pd.read_csv("mht_cet_cutoffs.csv")
        
        # Extract location from college name for filtering
        df['location'] = df['college_name'].apply(extract_location)
        
        return df
    
    # Fallback to JSON if CSV not available
    elif os.path.exists("mht_cet_cutoffs.json"):
        with open("mht_cet_cutoffs.json", "r") as f:
            data = json.load(f)
        
        # Convert to DataFrame with exploded cutoffs
        records = []
        for entry in data:
            for category, cutoff in entry["cutoffs"].items():
                record = {
                    "college_code": entry["college_code"],
                    "college_name": entry["college_name"],
                    "course_code": entry["course_code"],
                    "course_name": entry["course_name"],
                    "status": entry["status"],
                    "university": entry["university"],
                    "seat_type": entry["seat_type"],
                    "category": category,
                    "rank": cutoff["rank"],
                    "percentage": cutoff["percentage"]
                }
                records.append(record)
        
        df = pd.DataFrame(records)
        return df
    
    else:
        st.error("Data files not found. Please run the parser script first.")
        return None

# Function to extract location from college name
def extract_location(college_name):
    """Extract location from college name"""
    # List of common Maharashtra locations to look for
    locations = [
        "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Amravati", "Solapur", 
        "Kolhapur", "Sangli", "Satara", "Thane", "Navi Mumbai", "Ahmednagar", "Jalgaon", 
        "Dhule", "Nanded", "Chandrapur", "Akola", "Yavatmal", "Ratnagiri", "Raigad", 
        "Pimpri", "Chinchwad", "Wardha", "Latur", "Beed", "Parbhani", "Jalna"
    ]
    
    # Check if any of the locations are in the college name
    for location in locations:
        if location.lower() in college_name.lower():
            return location
    
    # If no match is found, return "Other"
    return "Other"

# Main application
def main():
    # Title and description
    st.title("🎓 MHT CET College Finder")
    st.markdown("""
    Find the best colleges based on MHT CET cutoff data. 
    This application helps you analyze the CAP Round-III cutoffs for engineering colleges in Maharashtra.
    """)
    
    # Load data
    df = load_data()
    if df is None:
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Category filter
    available_categories = sorted(df["category"].unique())
    selected_category = st.sidebar.selectbox(
        "Select Category",
        available_categories,
        index=0
    )
    
    # Course filter
    available_courses = sorted(df["course_name"].unique())
    selected_courses = st.sidebar.multiselect(
        "Select Courses",
        available_courses,
        default=available_courses[:3] if len(available_courses) >= 3 else available_courses
    )
    
    # College status filter
    available_statuses = sorted(df["status"].unique())
    selected_statuses = st.sidebar.multiselect(
        "Select College Status",
        available_statuses,
        default=available_statuses
    )
    
    # Seat type filter
    available_seat_types = sorted(df["seat_type"].unique())
    selected_seat_types = st.sidebar.multiselect(
        "Select Seat Type",
        available_seat_types,
        default=available_seat_types
    )
    
    # Rank range filter
    min_rank = int(df["rank"].min())
    max_rank = int(df["rank"].max())
    
    rank_range = st.sidebar.slider(
        "Rank Range",
        min_rank, max_rank,
        (min_rank, int(min_rank + (max_rank - min_rank) * 0.2))
    )
    
    # Location filter
    available_locations = sorted(df["location"].unique())
    selected_locations = st.sidebar.multiselect(
        "Select Locations",
        available_locations,
        default=available_locations
    )
    
    # Apply filters
    filtered_df = df[
        (df["category"] == selected_category) &
        (df["course_name"].isin(selected_courses)) &
        (df["status"].isin(selected_statuses)) &
        (df["seat_type"].isin(selected_seat_types)) &
        (df["location"].isin(selected_locations)) &
        (df["rank"] >= rank_range[0]) &
        (df["rank"] <= rank_range[1])
    ]
    
    # Sort by rank
    filtered_df = filtered_df.sort_values("rank")
    
    # Display results
    st.header("Top Colleges Based on Your Criteria")
    
    if len(filtered_df) == 0:
        st.warning("No colleges match your criteria. Try adjusting your filters.")
    else:
        # Show number of matching records
        # Show number of matching records
        st.info(f"Found {len(filtered_df)} matching records.")
        
        # Option to show all colleges or just top ones
        show_all_colleges = st.checkbox("Show all colleges", value=False)
        
        # Top colleges table
        if show_all_colleges:
            st.subheader("All Matching Colleges")
        else:
            st.subheader("Top 20 Colleges")
            
        display_cols = [
            "college_name", "course_name", "rank", "percentage", 
            "status", "seat_type", "location"
        ]
        
        if show_all_colleges:
            st.dataframe(filtered_df[display_cols], use_container_width=True)
        else:
            st.dataframe(filtered_df[display_cols].head(20), use_container_width=True)
        # Visualizations
        st.header("Visualizations")
        
        # Create tabs for different visualizations
        viz_tabs = st.tabs(["College Comparison", "Rank vs Percentage", "Course Comparison", "Category Analysis"])
        
        with viz_tabs[0]:
            st.subheader("Top 10 Colleges by Rank")
            
            # Get top 10 colleges for visualization
            top_10_colleges = filtered_df.head(10)
            
            if len(top_10_colleges) > 0:
                fig = px.bar(
                    top_10_colleges,
                    x="college_name",
                    y="rank",
                    color="course_name",
                    labels={"rank": "Cutoff Rank", "college_name": "College Name"},
                    title=f"Top 10 Colleges by Rank for {selected_category}",
                    hover_data=["percentage", "status", "seat_type", "location"],
                )
                # Customize layout
                fig.update_layout(xaxis_tickangle=-45)
                # Lower rank is better, so invert the y-axis
                fig.update_yaxes(autorange="reversed")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Not enough data for visualization.")
        
        with viz_tabs[1]:
            st.subheader("Rank vs Percentage Correlation")
            
            if len(filtered_df) > 0:
                fig = px.scatter(
                    filtered_df,
                    x="percentage",
                    y="rank",
                    color="college_name",
                    size="percentage",
                    hover_data=["course_name", "status", "seat_type", "location"],
                    labels={"rank": "Cutoff Rank", "percentage": "Cutoff Percentage"},
                )
                
                # Customize layout
                fig.update_layout(
                    xaxis=dict(title="Percentage (Higher is better)"),
                    yaxis=dict(title="Rank (Lower is better)", autorange="reversed")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add correlation analysis
                corr = filtered_df["rank"].corr(filtered_df["percentage"])
                st.info(f"Correlation between Rank and Percentage: {corr:.4f}")
            else:
                st.warning("Not enough data for visualization.")
        
        with viz_tabs[2]:
            st.subheader("Course Comparison")
            
            # Group by college and course to compare courses at the same college
            if len(filtered_df) > 0:
                # Get most popular colleges (having multiple courses)
                college_course_counts = filtered_df.groupby("college_name")["course_name"].nunique()
                colleges_with_multiple_courses = college_course_counts[college_course_counts > 1].index.tolist()
                
                if colleges_with_multiple_courses:
                    selected_college = st.selectbox(
                        "Select College for Course Comparison",
                        colleges_with_multiple_courses
                    )
                    
                    # Filter data for selected college
                    college_data = filtered_df[filtered_df["college_name"] == selected_college]
                    
                    # Create bar chart comparing courses
                    fig = px.bar(
                        college_data,
                        x="course_name",
                        y="rank",
                        color="course_name",
                        labels={"rank": "Cutoff Rank", "course_name": "Course Name"},
                        title=f"Course Comparison for {selected_college} ({selected_category})",
                        hover_data=["percentage", "status", "seat_type", "location"],
                        height=500
                    )
                    
                    # Customize layout
                    fig.update_layout(
                        xaxis_tickangle=-45,
                        xaxis=dict(title="Course"),
                        yaxis=dict(title="Rank (Lower is better)", autorange="reversed")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No colleges with multiple courses found in the filtered data.")
            else:
                st.warning("Not enough data for visualization.")
        
        with viz_tabs[3]:
            st.subheader("Multi-Category Analysis")
            
            # For this analysis, we need to get data for multiple categories
            # Let's allow the user to select multiple categories for comparison
            
            # Reset the category filter to include multiple categories
            multi_cat_select = st.multiselect(
                "Select Categories to Compare",
                available_categories,
                default=[selected_category] if selected_category else []
            )
            
            if multi_cat_select:
                # We'll need to get data for all selected categories
                multi_cat_data = df[
                    (df["category"].isin(multi_cat_select)) &
                    (df["course_name"].isin(selected_courses)) &
                    (df["status"].isin(selected_statuses)) &
                    (df["seat_type"].isin(selected_seat_types)) &
                    (df["rank"] >= rank_range[0]) &
                    (df["rank"] <= rank_range[1])
                ]
                
                if len(multi_cat_data) > 0:
                    # Let user select colleges to compare
                    top_n_colleges = st.slider("Number of top colleges to compare", 3, 15, 5)
                    
                    # Get top N colleges for each category based on rank
                    top_colleges_by_category = {}
                    all_top_colleges = set()
                    
                    for category in multi_cat_select:
                        cat_data = multi_cat_data[multi_cat_data["category"] == category]
                        if len(cat_data) > 0:
                            top_colleges = cat_data.sort_values("rank").head(top_n_colleges)["college_name"].unique().tolist()
                            top_colleges_by_category[category] = top_colleges
                            all_top_colleges.update(top_colleges)
                    
                    all_top_colleges = list(all_top_colleges)
                    
                    if all_top_colleges and len(all_top_colleges) <= 15:  # Limit to avoid overcrowding
                        # Create a pivot table for the heatmap
                        # For each college and category, find the best (minimum) rank
                        pivot_data = []
                        
                        for college in all_top_colleges:
                            for category in multi_cat_select:
                                cat_college_data = multi_cat_data[(multi_cat_data["category"] == category) & 
                                                                 (multi_cat_data["college_name"] == college)]
                                if len(cat_college_data) > 0:
                                    best_rank = cat_college_data["rank"].min()
                                    best_percentage = cat_college_data.loc[cat_college_data["rank"].idxmin(), "percentage"]
                                    pivot_data.append({
                                        "college_name": college,
                                        "category": category,
                                        "rank": best_rank,
                                        "percentage": best_percentage
                                    })
                        
                        if pivot_data:
                            pivot_df = pd.DataFrame(pivot_data)
                            
                            # Create heatmap using ranks
                            fig = px.density_heatmap(
                                pivot_df,
                                x="category",
                                y="college_name",
                                z="rank",
                                color_continuous_scale="RdYlGn_r",  # Reversed so lower ranks (better) are green
                                labels={"rank": "Cutoff Rank", "college_name": "College", "category": "Category"},
                                title=f"College Ranks Across Different Categories",
                                height=600
                            )
                            
                            # Add customized hover information with both rank and percentage
                            hover_temp = "<b>%{y}</b><br>" + \
                                         "Category: %{x}<br>" + \
                                         "Rank: %{z}<br>" + \
                                         "<extra></extra>"
                            fig.update_traces(hovertemplate=hover_temp)
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add explanation
                            st.info("The heatmap shows cutoff ranks across different categories. " + 
                                   "Darker colors represent better ranks (lower numbers).")
                            
                            # Also create a grouped bar chart for better comparison
                            fig2 = px.bar(
                                pivot_df,
                                x="college_name",
                                y="rank",
                                color="category",
                                barmode="group",
                                labels={"rank": "Cutoff Rank", "college_name": "College", "category": "Category"},
                                title=f"College Ranks Across Different Categories",
                                height=500
                            )
                            
                            # Customize layout
                            fig2.update_layout(
                                xaxis_tickangle=-45,
                                yaxis=dict(autorange="reversed")  # Lower rank is better
                            )
                            
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.warning("Not enough data for comparison across categories.")
                    elif len(all_top_colleges) > 15:
                        st.warning("Too many colleges to display in a heatmap. Please select fewer categories or reduce the number of top colleges.")
                    else:
                        st.warning("No colleges found in the selected categories.")
                else:
                    st.warning("No data available for the selected categories.")
            else:
                st.warning("Please select at least one category for analysis.")

# Run the app
if __name__ == "__main__":
    main()
